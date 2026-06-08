from django.db import models
from drivers.models import DriverProfile
from wallets.models import ReferralReward

class DriverProfileService:
    """سرویس مدیریت پروفایل راننده"""

    @staticmethod
    def get_queryset(user):
        """
        برگرداندن پروفایل‌ها بر اساس نقش کاربر.
        - ادمین: همهٔ پروفایل‌ها
        - راننده: فقط پروفایل خودش
        """
        if not user.is_authenticated:
            return DriverProfile.objects.none()
        if user.is_staff:
            return DriverProfile.objects.all()
        return DriverProfile.objects.filter(user=user)

    @staticmethod
    def get_profile(user) -> DriverProfile:
        """
        دریافت پروفایل کاربر (یا None اگر وجود نداشته باشد).
        """
        return DriverProfile.objects.filter(user=user).first()

    @staticmethod
    def accept_contract(profile: DriverProfile) -> DriverProfile:
        """
        پذیرش قرارداد (مرحلهٔ ۴ ثبت‌نام).
        Args:
            profile: پروفایل راننده
        Returns:
            پروفایل به‌روزرسانی‌شده
        Raises:
            ValueError: اگر احراز هویت تأیید نشده باشد
        """
        if profile.kyc_status != 'APPROVED':
            raise ValueError("ابتدا باید احراز هویت شما تأیید شود")

        profile.is_contract_accepted = True
        profile.registration_step = DriverProfile.RegistrationStep.CONTRACT
        profile.save()
        return profile

    @staticmethod
    def get_referral_summary(driver: DriverProfile) -> dict:
        """
        خلاصهٔ دعوت‌ها و جوایز معرف.
        """
        invited_count = ReferralReward.objects.filter(driver=driver).count()
        total_rewards = ReferralReward.objects.filter(driver=driver).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        rewards = ReferralReward.objects.filter(driver=driver).values(
            'amount', 'created_at', 'referred_driver__full_name'
        ).order_by('-created_at')

        return {
            'referral_code': driver.referral_code,
            'invited_count': invited_count,
            'total_rewards': total_rewards,
            'rewards': list(rewards),
        }

    @staticmethod
    def apply_referral_code(user, code: str) -> dict:
        """
        Apply a referral code to a driver.

        Args:
            user: The authenticated user (must have a driver_profile)
            code: The referral code to apply

        Returns:
            dict: {'message': '...'}

        Raises:
            ValueError: if code is empty, invalid, or driver already referred
        """
        if not code:
            raise ValueError("کد معرف الزامی است")

        try:
            referrer = DriverProfile.objects.get(referral_code=code)
        except DriverProfile.DoesNotExist:
            raise ValueError("کد معرف نامعتبر است")

        driver = user.driver_profile

        if driver.referred_by:
            raise ValueError("شما قبلاً توسط یک راننده دیگر دعوت شده‌اید")

        driver.referred_by = referrer
        driver.save()

        return {'message': 'کد معرف با موفقیت ثبت شد'}