import random
# import json
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework import status, viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from services.tasks import send_otp_sms_task
from .serializers import (UserSerializer, OTPRequestSerializer, OTPVerifySerializer)
from .models import OTP
from permissions import IsOwnerOrAdmin


User = get_user_model()


# ===============
# User
# ===============


class UserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    def get(self, request):
        user = request.user  # کاربر جاری که نیاز داریم اطلاعاتش رو برگردونیم
        serializer = UserSerializer(user)
        return Response(serializer.data)


class RequestOTPView(APIView):
    """
    api برای درخواست کد احراز هویت
    برای ایجاد کاربر جدید به هنگام درخواست کد
    """
    serializer_class = OTPRequestSerializer
    throttle_classes = [AnonRateThrottle]
    throttle_scope = 'otp_request'

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['identifier']
            purpose = serializer.validated_data['purpose']

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
                send_otp_sms_task.delay(phone=identifier, code=otp_instance.code)
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

