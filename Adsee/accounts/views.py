import random
# import json
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404
# from django.core import cache
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework import status, viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from utils import send_otp_sms, send_kyc_to_external_service
from .serializers import (UserSerializer, OTPRequestSerializer, OTPVerifySerializer, DriverProfileSerializer,
                          ClientProfileSerializer, DriverDocumentSerializer, DriverProfileKycUpdateSerializer,
                          DriverProfileKycStatusSerializer,
                          )
from .models import OTP, DriverProfile, ClientProfile, DriverDocument
from permissions import IsClientUser, IsDriverUser, IsOwnerOrAdmin


User = get_user_model()


# ===============
# User
# ===============


class UserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    def get(self, request):
        user = request.user  # کاربر جاری که نیاز داریم اطلاعاتش رو برگردونیم
        serializer = UserSerializer(user)
        return Response(serializer.data)


class RequestOTPView(APIView):
    serializer_class = OTPRequestSerializer
    throttle_classes = [AnonRateThrottle]
    throttle_scope = 'otp_request'

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            purpose = serializer.validated_data['purpose']

            # # --- Cache logic for rate limiting ---
            # cache_key_base = f"otp:{purpose}:{identifier}"
            # attempts_key = f"{cache_key_base}:attempts"
            # cooldown_key = f"{cache_key_base}:cooldown"
            #
            # # Check cooldown period
            # cooldown_active = cache.get(cooldown_key)
            # if cooldown_active:
            #     return Response(
            #         {"detail": "Please wait a moment before trying again."},
            #         status=status.HTTP_429_TOO_MANY_REQUESTS
            #     )
            #
            # # Check number of attempts (e.g., max 3 attempts in 5 minutes)
            # max_attempts = 3
            # attempt_window_seconds = 120 # 5 minutes
            # current_attempts = cache.get(attempts_key, 0)
            #
            # if current_attempts >= max_attempts:
            #     # Start cooldown if max attempts reached
            #     cache.set(cooldown_key, True, timeout=300) # 10 minutes cooldown
            #     return Response(
            #         {"detail": "Too many attempts. Please try again later."},
            #         status=status.HTTP_429_TOO_MANY_REQUESTS
            #     )
            #
            # # Increment attempt count
            # cache.set(attempts_key, current_attempts + 1, timeout=attempt_window_seconds)

            # حذف OTP های قدیمی برای همین identifier و purpose (اگر باشد)
            OTP.objects.filter(identifier=identifier, purpose=purpose, used=False, expires_at__gt=timezone.now()).delete()

            # تولید OTP
            otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            # print(otp_code,int(settings.OTP_CODE_EXPIRY_MINUTES))
            expires_at = timezone.now() + timezone.timedelta(minutes=int(settings.OTP_CODE_EXPIRY_MINUTES))

            # ذخیره OTP در دیتابیس
            # اگر کاربر از قبل وجود دارد، آن را به OTP وصل کن (برای مورد LOGIN)
            user = User.objects.get(phone=identifier)
            if not user:
                user = User.objects.create_user(phone=identifier, is_active=True)

            otp_instance = OTP.objects.create(
                identifier=identifier,
                purpose=purpose,
                code=otp_code,
                expires_at=expires_at,
                user=user # اینجا user را اگر پیدا شد، وصل می‌کنیم
            )

            # ارسال SMS
            try:
                response = send_otp_sms(identifier, otp_code)
            except Exception as e:
                # در اینجا باید خطا را لاگ کنید و یک پاسخ مناسب بدهید
                # این مرحله نباید باعث شود OTP ذخیره نشود
                print(f"Error sending SMS: {e}")
                return Response({"detail": "Failed to send OTP. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(
                {"detail": f"OTP sent successfully to {identifier}. It will expire in {settings.OTP_CODE_EXPIRY_MINUTES} minutes."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    serializer_class = OTPVerifySerializer
    throttle_classes = [AnonRateThrottle]
    throttle_scope = 'otp_verify'

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            otp_code = serializer.validated_data['otp']
            purpose = request.data.get('purpose', OTP.Purpose.LOGIN) # اگر purpose ارسال نشده، پیش‌فرض LOGIN

            try:
                otp_instance = OTP.objects.get(
                    identifier=identifier,
                    purpose=purpose,
                    code=otp_code,
                    used=False,
                    expires_at__gt=timezone.now()
                )
            except OTP.DoesNotExist:
                return Response({"detail": "Invalid OTP or expired."}, status=status.HTTP_400_BAD_REQUEST)

            # OTP معتبر است
            otp_instance.mark_used() # OTP را به عنوان استفاده شده علامت بزن

            user = otp_instance.user

            if purpose == OTP.Purpose.LOGIN:
                if not user:
                    # اگر OTP برای لاگین بود ولی user مرتبط نداشتیم (نباید پیش بیاید اگر منطق RequestOTP درست باشد)
                    return Response({"detail": "User not found. Please register first."}, status=status.HTTP_400_BAD_REQUEST)
                if not user.is_active:
                    return Response({"detail": "User account is inactive."}, status=status.HTTP_403_FORBIDDEN)

                # اینجا کاربر لاگین می‌شود (با استفاده از Simple JWT)
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data # اطلاعات کاربر را هم برگردان (اختیاری)
                }, status=status.HTTP_200_OK)

            elif purpose == OTP.Purpose.REGISTER:
                # اگر OTP برای ثبت نام بود، یعنی کاربر قبلاً ثبت نشده
                # باید کاربر را بسازیم
                if User.objects.filter(identifier=identifier).exists():
                     # اگر اتفاقی کاربر با این identifier از قبل وجود دارد (ولی OTP مرتبط نبود)
                    return Response({"detail": "User with this identifier already exists. Please use Login."}, status=status.HTTP_409_CONFLICT)

                new_user = User.objects.create_user(phone=identifier, password=None, is_active=True) #password=None چون با OTP لاگین میشه

                refresh = RefreshToken.for_user(new_user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(new_user).data
                }, status=status.HTTP_201_CREATED)

            # انواع purpose های دیگر را اینجا اضافه کنید (مثل VERIFY_PROFILE)

            else:
                return Response({"detail": "Unsupported OTP purpose."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Driver Profile


class DriverProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = DriverProfile.objects.all()
    serializer_class = DriverProfileSerializer
    permission_classes = [IsAuthenticated, IsDriverUser]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    def get_object(self):
        user = self.request.user
        if user.is_anonymous:
            return None

        try:
            driver_profile = DriverProfile.objects.get(user=user)
            return driver_profile
        except DriverProfile.DoesNotExist:
            raise Http404("Driver profile not found for this user.")

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            raise Http404("user not found.")


class DriverDocumentUploadView(APIView):
    """
    API برای آپلود مدارک توسط راننده.
    """
    permission_classes = [IsAuthenticated, IsDriverUser]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # اگر نیاز است که همزمان چندین مدرک آپلود شود، این منطق باید تغییر کند
        # در حال حاضر فرض می‌کنیم کاربر یک مدرک در هر درخواست آپلود می‌کند

        serializer = DriverDocumentSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            document_type = request.data.get('document_type')
            if not document_type:
                 return Response(
                    {"detail": "Document type is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # بررسی اینکه آیا این نوع مدرک قبلاً توسط کاربر آپلود شده است
            existing_document = DriverDocument.objects.filter(
                user=request.user,
                document_type=document_type
            ).first()

            if existing_document and existing_document.status != DriverDocument.ApprovalStatus.REJECTED:
                # اگر مدرک از قبل وجود دارد و رد نشده، اجازه آپلود مجدد نمی‌دهیم مگر اینکه بخواهیم overwrite کنیم
                # یا می‌توانیم اینجا منطق overwrite را اضافه کنیم
                 return Response(
                    {"detail": f"A document of type '{document_type}' already exists and is not rejected. Please update it if necessary."},
                    status=status.HTTP_409_CONFLICT
                )

            # ایجاد یا به‌روزرسانی مدرک
            document = serializer.save(user=request.user)

            # به‌روزرسانی وضعیت کلی KYC پروفایل راننده
            driver_profile, created = DriverProfile.objects.get_or_create(user=request.user)
            if driver_profile.kyc_status == DriverProfile.KYCStatus.NOT_STARTED:
                driver_profile.kyc_status = DriverProfile.KYCStatus.PENDING
                driver_profile.kyc_submitted_at = timezone.now()
                driver_profile.save()
            elif driver_profile.kyc_status == DriverProfile.KYCStatus.REJECTED:
                # اگر پروفایل قبلاً رد شده بود و کاربر مدارک جدید آپلود می‌کنه، وضعیت رو به PENDING برمی‌گردونیم
                driver_profile.kyc_status = DriverProfile.KYCStatus.PENDING
                driver_profile.kyc_reject_reason = None # پاک کردن دلیل رد قبلی
                driver_profile.kyc_submitted_at = timezone.now() # یا تنظیم زمان اولین ارسال
                driver_profile.save()

            try:
                response = send_kyc_to_external_service(driver_profile, document)
            except:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DriverKycStatusView(APIView):
    """
    API برای نمایش وضعیت کلی KYC و جزئیات مدارک آپلود شده توسط راننده.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, *args, **kwargs):
        try:
            driver_profile = DriverProfile.objects.get(user=request.user)
            # فیلتر کردن مدارکی که متعلق به این کاربر هستند
            documents = DriverDocument.objects.filter(user=request.user).order_by('-submitted_at')

            serializer = DriverProfileKycStatusSerializer(driver_profile)
            data = serializer.data
            # اضافه کردن لیست مدارک به پاسخ
            data['documents'] = DriverDocumentSerializer(documents, many=True).data

            return Response(data, status=status.HTTP_200_OK)

        except DriverProfile.DoesNotExist:
            return Response(
                {"detail": "Driver profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class DriverProfileKycAdminView(APIView):
    """
    API برای ادمین جهت بررسی، تأیید یا رد مدارک و پروفایل راننده.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]  # فرض می‌کنیم IsAdminUser را داریم

    def get(self, request, user_id, format=None):
        """
        نمایش پروفایل و مدارک یک راننده خاص توسط ادمین.
        """
        try:
            user = settings.AUTH_USER_MODEL.objects.get(id=user_id)
            driver_profile = DriverProfile.objects.get(user=user)
            documents = DriverDocument.objects.filter(user=user).order_by('-submitted_at')

            profile_serializer = DriverProfileKycStatusSerializer(driver_profile)
            doc_serializer = DriverDocumentSerializer(documents, many=True)

            response_data = profile_serializer.data
            response_data['documents'] = doc_serializer.data
            response_data['user_id'] = user.id
            response_data['username'] = user.username

            return Response(response_data, status=status.HTTP_200_OK)

        except settings.AUTH_USER_MODEL.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except DriverProfile.DoesNotExist:
            return Response({"detail": "Driver profile not found for this user."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, user_id, format=None):
        """
        تأیید یا رد مدارک و پروفایل راننده توسط ادمین.
        'action': 'approve' or 'reject'
        'document_id': (optional) ID مدرک برای تأیید/رد جزئی
        'reject_reason': (optional) دلیل رد شدن
        """
        action = request.data.get('action')
        document_id = request.data.get('document_id')
        reject_reason = request.data.get('reject_reason', '')

        try:
            user = settings.AUTH_USER_MODEL.objects.get(id=user_id)
            driver_profile = DriverProfile.objects.get(user=user)
        except settings.AUTH_USER_MODEL.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except DriverProfile.DoesNotExist:
            return Response({"detail": "Driver profile not found for this user."}, status=status.HTTP_404_NOT_FOUND)

        if action == 'approve':
            if document_id:
                # تأیید یک مدرک خاص
                try:
                    document = DriverDocument.objects.get(id=document_id, user=user)
                    if document.status == DriverDocument.ApprovalStatus.REJECTED:
                        # اگر مدرک رد شده بود و الان تایید میشه، دلیل رد رو پاک می‌کنیم
                        document.reject_reason = None
                    document.status = DriverDocument.ApprovalStatus.APPROVED
                    document.reviewed_at = timezone.now()
                    document.save()
                except DriverDocument.DoesNotExist:
                    return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
            else:
                # تأیید کلی پروفایل (اگر همه مدارک تأیید شده باشند)
                all_documents_approved = DriverDocument.objects.filter(user=user,
                                                                 status=DriverDocument.ApprovalStatus.PENDING).count() == 0
                if not all_documents_approved:
                    return Response(
                        {"detail": "Cannot approve profile. Some documents are still pending."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                driver_profile.kyc_status = DriverProfile.KYCStatus.APPROVED
                driver_profile.kyc_reject_reason = None
                driver_profile.kyc_reviewed_at = timezone.now()
                driver_profile.save()

        elif action == 'reject':
            if document_id:
                # رد یک مدرک خاص
                try:
                    document = DriverDocument.objects.get(id=document_id, user=user)
                    document.status = DriverDocument.ApprovalStatus.REJECTED
                    document.reject_reason = reject_reason
                    document.reviewed_at = timezone.now()
                    document.save()
                except DriverDocument.DoesNotExist:
                    return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
            else:
                # رد کلی پروفایل
                driver_profile.kyc_status = DriverProfile.KYCStatus.REJECTED
                driver_profile.kyc_reject_reason = reject_reason
                driver_profile.kyc_reviewed_at = timezone.now()
                driver_profile.save()
                # مهم: اگر پروفایل رد شد، باید وضعیت همه مدارک نامشخص رو هم به REJECTED تغییر داد؟ یا نه؟
                # این بستگی به منطق کسب و کار داره. اینجا فعلا فقط پروفایل رو رد می‌کنیم.
                # Document.objects.filter(user=user, status=Document.ApprovalStatus.PENDING).update(
                #     status=Document.ApprovalStatus.REJECTED,
                #     reject_reason=reject_reason,
                #     reviewed_at=timezone.now()
                # )

        else:
            return Response({"detail": "Invalid action. Use 'approve' or 'reject'."},
                            status=status.HTTP_400_BAD_REQUEST)

        # پس از هر عملیات، وضعیت کلی KYC را مجدد محاسبه و به‌روزرسانی می‌کنیم
        self._update_overall_kyc_status(driver_profile)

        return Response({"detail": f"Action '{action}' processed successfully."}, status=status.HTTP_200_OK)

    def _update_overall_kyc_status(self, driver_profile):
        """
        تابع کمکی برای به‌روزرسانی وضعیت کلی KYC بر اساس وضعیت تمام مدارک.
        """
        user = driver_profile.user
        documents = DriverDocument.objects.filter(user=user)

        if not documents.exists():
            # اگر هیچ مدرکی آپلود نشده
            driver_profile.kyc_status = DriverProfile.KYCStatus.NOT_STARTED
            driver_profile.kyc_reject_reason = None
            driver_profile.kyc_reviewed_at = None
            driver_profile.kyc_submitted_at = None
            driver_profile.save()
            return

        pending_docs = documents.filter(status=DriverDocument.ApprovalStatus.PENDING).exists()
        rejected_docs = documents.filter(status=DriverDocument.ApprovalStatus.REJECTED).exists()
        approved_docs_count = documents.filter(status=DriverDocument.ApprovalStatus.APPROVED).count()
        total_docs_count = documents.count()

        if rejected_docs:
            # اگر حتی یک مدرک رد شده باشد، وضعیت کلی رد می‌شود
            driver_profile.kyc_status = DriverProfile.KYCStatus.REJECTED
            # جمع‌آوری دلایل رد همه مدارک رد شده
            reasons = documents.filter(status=DriverDocument.ApprovalStatus.REJECTED).values_list('reject_reason', flat=True)
            driver_profile.kyc_reject_reason = ". ".join(filter(None, reasons))  # حذف دلایل خالی
            driver_profile.kyc_reviewed_at = timezone.now()  # زمان آخرین بازبینی
        elif pending_docs:
            # اگر مدرکی در انتظار بررسی باشد
            driver_profile.kyc_status = DriverProfile.KYCStatus.PENDING
            driver_profile.kyc_reject_reason = None
            driver_profile.kyc_reviewed_at = None  # یا زمان آخرین مدرک PENDING
            driver_profile.kyc_submitted_at = driver_profile.kyc_submitted_at or timezone.now()  # تنظیم زمان اولین ارسال اگر قبلا تنظیم نشده
        elif approved_docs_count == total_docs_count:
            # اگر همه مدارک تأیید شده باشند
            driver_profile.kyc_status = DriverProfile.KYCStatus.APPROVED
            driver_profile.kyc_reject_reason = None
            driver_profile.kyc_reviewed_at = timezone.now()  # زمان آخرین بازبینی
        else:
            # حالت پیش‌فرض یا دیگر حالات غیرمنتظره
            driver_profile.kyc_status = DriverProfile.KYCStatus.NOT_STARTED
            driver_profile.kyc_reject_reason = None
            driver_profile.kyc_reviewed_at = None

        driver_profile.save()


# class KycWebhookReceiverView(APIView):
#     # permission_classes = [...] # برای اطمینان از اینکه فقط سرویس خارجی می‌تواند به این API دسترسی داشته باشد
#
#     def post(self, request):
#         data = request.data
#         request_id = data.get('request_id')
#         status = data.get('status')
#         reject_reason = data.get('reject_reason', '')
#
#         try:
#             kyc_request = KycVerificationRequest.objects.get(external_request_id=request_id)
#
#             kyc_request.status = status
#             kyc_request.reject_reason = reject_reason
#             if status in ['APPROVED', 'REJECTED']:
#                 kyc_request.reviewed_at = timezone.now()
#             kyc_request.save()
#
#             # بروزرسانی وضعیت کلی DriverProfile
#             profile = kyc_request.driver_profile
#             if status == 'APPROVED':
#                 profile.kyc_status = 'APPROVED'
#                 profile.kyc_reject_reason = None
#             elif status == 'REJECTED':
#                 profile.kyc_status = 'REJECTED'
#                 profile.kyc_reject_reason = reject_reason
#             else: # PENDING
#                 profile.kyc_status = 'PENDING'
#             profile.kyc_reviewed_at = timezone.now()
#             profile.save()
#
#             return Response({'message': 'Webhook received successfully.'}, status=status.HTTP_200_OK)
#
#         except KycVerificationRequest.DoesNotExist:
#             return Response({'error': 'KycVerificationRequest not found.'}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# Client Profile


class ClientProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated, IsClientUser]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    def process_kyc(self, instance):
        document = instance.id_or_registration_copy
        if not document:
            return
        # existing_document = DriverDocument.objects.filter(
        #     user=instance.user,
        #     document_type=document
        # ).first()
        # if existing_document and existing_document.status != instance.KYCStatus.REJECTED:
        #     # اگر مدرک از قبل وجود دارد و رد نشده، اجازه آپلود مجدد نمی‌دهیم مگر اینکه بخواهیم overwrite کنیم
        #     # یا می‌توانیم اینجا منطق overwrite را اضافه کنیم
        #     return Response(
        #         {
        #             "detail":
        #             f"A document of type '{document}' already exists and is not rejected.
        #             Please update it if necessary."},
        #         status=status.HTTP_409_CONFLICT
        #     )
        try:
            response = send_kyc_to_external_service(instance, document)
        except:
            return
        return response

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'POST':
            try:
                kwargs['data']['user'] = self.request.user.pk
            except:
                pass
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save()
        # self.process_kyc(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        # self.process_kyc(instance)

    def get_object(self):
        user = self.request.user
        if user.is_anonymous:
            return None

        try:
            client_profile = ClientProfile.objects.get(user=user)
            return client_profile
        except ClientProfile.DoesNotExist:
            raise Http404("Client profile not found for this user.")

    def perform_create(self, serializer):
        # اگر در درخواست، user مشخص شده باشد، از آن استفاده کن
        user_id = self.request.data.get('user')
        if user_id:
            try:
                user = get_object_or_404(get_user_model(), pk=user_id)
                serializer.save(user=user)
            except ValueError:  # اگر user_id عدد نباشد
                raise serializers.ValidationError({"user": "شناسه کاربر نامعتبر است."})
        else:
            # اگر user مشخص نشده باشد، باید خطا بدهد (چون برای ادمین هم الزامی است)
            raise serializers.ValidationError({"user": "شناسه کاربر الزامی است."})
