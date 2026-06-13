import random
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers import UserSerializer
from rest_framework import status
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import OTP
from services.tasks import send_otp_sms_task

User = get_user_model()


class OTPService:
    """سرویس مدیریت OTP"""

    @staticmethod
    def generate_otp_code(length=6) -> str:
        """تولید کد تصادفی عددی"""
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])

    @staticmethod
    def get_or_create_user(phone: str):
        """
        یافتن کاربر با شماره تلفن یا ساخت کاربر جدید
        Returns: (user, created)
        """
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={'is_active': True}
        )
        return user, created

    @staticmethod
    def delete_existing_otps(identifier: str, purpose: str):
        """حذف OTP‌های معتبر قبلی برای همین شماره و هدف"""
        OTP.objects.filter(
            identifier=identifier,
            purpose=purpose,
            used=False,
            expires_at__gt=timezone.now()
        ).delete()

    @staticmethod
    def create_otp(identifier: str, purpose: str, user=None) -> OTP:
        """
        ایجاد یک OTP جدید
        Args:
            identifier: شماره تلفن
            purpose: هدف (LOGIN, REGISTER, ...)
            user: کاربر مرتبط (در صورت وجود)
        Returns: نمونهٔ OTP ساخته‌شده
        """
        code = OTPService.generate_otp_code()
        expires_at = timezone.now() + timezone.timedelta(
            minutes=int(settings.OTP_CODE_EXPIRY_MINUTES)
        )
        otp = OTP.objects.create(
            identifier=identifier,
            purpose=purpose,
            code=code,
            expires_at=expires_at,
            user=user
        )
        return otp

    @staticmethod
    def send_otp_sms(phone: str, code: str):
        """
        ارسال کد OTP از طریق پیامک (Celery task)
        Raises: Exception در صورت خطا در صف
        """
        send_otp_sms_task.delay(phone=phone, code=code)


    @classmethod
    def request_otp(cls, identifier: str, purpose: str):
        """
        جریان کامل درخواست OTP:
        ۱. حذف OTP‌های قبلی
        ۲. پیدا کردن / ایجاد کاربر
        ۳. تولید کد جدید
        ۴. ارسال پیامک
        Returns: (otp_instance, created_user_flag)
        """
        # ۱. حذف OTP‌های معتبر قبلی
        cls.delete_existing_otps(identifier, purpose)
        # ۲. یافتن یا ساخت کاربر
        user, created = cls.get_or_create_user(identifier)
        # ۳. ایجاد OTP جدید
        otp = cls.create_otp(identifier, purpose, user=user)
        # ۴. ارسال SMS
        try:
            cls.send_otp_sms(identifier, otp.code)
        except Exception as e:
            # اگر ارسال پیامک شکست خورد، OTP را حذف نکنیم،
            # اما خطا را به لایهٔ بالا اعلام کنیم
            raise Exception(f"SMS sending failed: {e}")
        return otp, created

    @classmethod
    def verify_otp(cls, identifier: str, otp_code: str, purpose: str):
        """
        تأیید کد OTP و برگرداندن توکن در صورت موفقیت
        Returns: (data_dict, http_status)
        """
        # ۱. یافتن OTP معتبر
        try:
            otp_instance = OTP.objects.get(
                identifier=identifier,
                purpose=purpose,
                code=otp_code,
                used=False,
                expires_at__gt=timezone.now()
            )
        except OTP.DoesNotExist:
            return {"detail": "کد تأیید نامعتبر یا منقضی شده است."}, status.HTTP_400_BAD_REQUEST

        # ۲. علامت‌گذاری OTP به‌عنوان استفاده‌شده
        otp_instance.mark_used()

        user = otp_instance.user

        # ۳. مدیریت بر اساس نوع purpose
        if purpose == OTP.Purpose.LOGIN:
            if not user:
                return {"detail": "کاربر یافت نشد. لطفاً ابتدا ثبت‌نام کنید."}, status.HTTP_400_BAD_REQUEST
            if not user.is_active:
                return {"detail": "حساب کاربری غیرفعال است."}, status.HTTP_403_FORBIDDEN

            refresh = RefreshToken.for_user(user)
            return {
                       'refresh': str(refresh),
                       'access': str(refresh.access_token),
                       'user': UserSerializer(user).data
                   }, status.HTTP_200_OK

        elif purpose == OTP.Purpose.REGISTER:
            # اگر کاربری با این شماره از قبل وجود دارد (و OTP مرتبط نبود)
            if User.objects.filter(phone=identifier).exists():
                return {"detail": "این شماره قبلاً ثبت شده است. لطفاً وارد شوید."}, status.HTTP_409_CONFLICT

            # ایجاد کاربر جدید
            new_user = User.objects.create_user(
                phone=identifier,
                password=None,  # بدون رمز عبور، چون با OTP وارد می‌شود
                is_active=True
            )
            refresh = RefreshToken.for_user(new_user)
            return {
                       'refresh': str(refresh),
                       'access': str(refresh.access_token),
                       'user': UserSerializer(new_user).data
                   }, status.HTTP_201_CREATED

        # می‌توانی purposes دیگر (مثل VERIFY_PROFILE) را اینجا اضافه کنی

        return {"detail": "هدف نامعتبر است."}, status.HTTP_400_BAD_REQUEST