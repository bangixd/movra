from .models import DriverProfile, DriverDocument
from .serializers import DriverProfileSerializer, DriverDocumentSerializer, DriverProfileKycUpdateSerializer,\
    DriverProfileKycStatusSerializer
from permissions import IsDriverUser, IsOwnerOrAdmin
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, viewsets, serializers
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAuthenticated
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from utils import send_kyc_to_external_service



class DriverProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = DriverProfile.objects.all()
    serializer_class = DriverProfileSerializer
    permission_classes = [IsDriverUser, IsOwnerOrAdmin]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    # def get_object(self):
    #     user = self.request.user
    #     if user.is_anonymous:
    #         return None
    #
    #     try:
    #         driver_profile = DriverProfile.objects.get(user=user)
    #         return driver_profile
    #     except DriverProfile.DoesNotExist:
    #         raise Http404("Driver profile not found for this user.")

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            raise Http404("user not found.")


class DriverDocumentUploadView(APIView):
    """
    API برای آپلود مدارک توسط راننده.
    """
    permission_classes = [IsAuthenticated, IsDriverUser, IsOwnerOrAdmin]
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
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin, IsOwnerOrAdmin]

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
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin, IsOwnerOrAdmin]  # فرض می‌کنیم IsAdminUser را داریم

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
