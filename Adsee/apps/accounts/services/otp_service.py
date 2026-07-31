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
    def generate_otp_code(length=4) -> str:
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
        # حذف OTP‌های معتبر قبلی برای همین شماره و هدف
        cls.delete_existing_otps(identifier, purpose)

        # یافتن کاربر (اگر وجود داشته باشد) ولی بدون خطا
        user = User.objects.filter(phone=identifier).first()

        # ایجاد OTP جدید (user می‌تواند None باشد – در verify پر می‌شود)
        otp = cls.create_otp(identifier, purpose, user=user)

        # ارسال SMS
        try:
            cls.send_otp_sms(identifier, otp.code)
        except Exception as e:
            raise Exception(f"SMS sending failed: {e}")

        return otp, user is not None  # True اگر کاربر وجود داشت

    # @classmethod
    # def request_otp(cls, identifier: str, purpose: str):
    #     # حذف OTP‌های قبلی
    #     cls.delete_existing_otps(identifier, purpose)
    #
    #     # فقط اگر کاربر از قبل وجود داشته باشد، او را پیدا کن
    #     # برای ثبت‌نام، کاربر جدید نسازیم
    #     user = None
    #     if purpose != OTP.Purpose.REGISTER:
    #         user = User.objects.filter(phone=identifier).first()
    #         if not user and purpose == OTP.Purpose.LOGIN:
    #             # برای ورود هم می‌توانیم خطا بدهیم (کاربر باید وجود داشته باشد)
    #             raise ValueError("کاربری با این شماره یافت نشد.")
    #         # اگر VERIFY_PROFILE باشد، کاربر باید وجود داشته باشد
    #         if not user and purpose == OTP.Purpose.VERIFY_PROFILE:
    #             raise ValueError("کاربری با این شماره یافت نشد.")
    #     # برای REGISTER، user = None (در مرحلهٔ تأیید ساخته می‌شود)
    #
    #     # ایجاد OTP جدید (بدون اتصال کاربر برای REGISTER)
    #     otp = cls.create_otp(identifier, purpose, user=user)
    #
    #     # ارسال SMS
    #     try:
    #         cls.send_otp_sms(identifier, otp.code)
    #     except Exception as e:
    #         raise Exception(f"SMS sending failed: {e}")
    #
    #     return otp, user is not None  # created flag (True if user existed)

    @classmethod
    def verify_otp(cls, identifier: str, otp_code: str, purpose: str, role: str):
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
            if user:
                if not user.is_active:
                    return {"detail": "حساب کاربری غیرفعال است."}, status.HTTP_403_FORBIDDEN
            else:
                role = role if role else User.Role.CLIENT
                user = User.objects.create_user(phone=identifier, role=role, is_active=True)

            refresh = RefreshToken.for_user(user)
            return {
                       'refresh': str(refresh),
                       'access': str(refresh.access_token),
                       'user': UserSerializer(user).data
                   }, status.HTTP_200_OK

        elif purpose == OTP.Purpose.REGISTER:
            # کاربر نباید از قبل وجود داشته باشد
            if User.objects.filter(phone=identifier).exists():
                return {"detail": "این شماره قبلاً ثبت شده است. لطفاً وارد شوید."}, status.HTTP_409_CONFLICT

            # ایجاد کاربر جدید با نقش داده‌شده یا پیش‌فرض
            new_user = User.objects.create_user(
                phone=identifier,
                password=None,
                is_active=True,
                role=role if role else User.Role.CLIENT
            )
            refresh = RefreshToken.for_user(new_user)
            return {
                       'refresh': str(refresh),
                       'access': str(refresh.access_token),
                       'user': UserSerializer(new_user).data
                   }, status.HTTP_201_CREATED

        # می‌توانی purposes دیگر (مثل VERIFY_PROFILE) را اینجا اضافه کنی

        return {"detail": "هدف نامعتبر است."}, status.HTTP_400_BAD_REQUEST