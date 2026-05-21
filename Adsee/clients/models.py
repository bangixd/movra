from django.db import models
from accounts.models import User
from django.utils import timezone
from django.core.validators import RegexValidator


class ClientProfile(models.Model):
    class AdvertiserType(models.TextChoices):
        REAL = "REAL", "Real"
        LEGAL = "LEGAL", "Legal"

    class KYCStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile")

    # -----------------------
    # 1) نوع تبلیغ‌دهنده
    # -----------------------
    advertiser_type = models.CharField(
        max_length=10, choices=AdvertiserType.choices, default=AdvertiserType.REAL
    )

    # -----------------------
    # 2) اطلاعات هویتی
    # -----------------------
    # حقیقی
    full_name = models.CharField(max_length=120, blank=True, null=True)
    national_id = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r"^\d{10}$", message="کد ملی باید ۱۰ رقمی باشد.")],
        help_text="برای حقیقی: کد ملی ۱۰ رقمی"
    )

    # حقوقی
    company_name = models.CharField(max_length=150, blank=True, null=True)
    national_economic_code = models.CharField(max_length=15, blank=True, null=True)  # کد اقتصادی (اختیاری ولی پیشنهاد می‌شود)
    registration_number = models.CharField(max_length=50, blank=True, null=True)    # شماره ثبت (اختیاری ولی پیشنهاد می‌شود)

    # -----------------------
    # 3) مدارک احراز هویت (KYC پایه/کم‌سخت‌گیرانه)
    # -----------------------
    avatar = models.ImageField(upload_to="clients/avatars/", blank=True, null=True)

    # یک مدرک پایه کافی باشد (کارت ملی برای حقیقی یا مدرک ثبت/مجوز برای حقوقی)
    id_or_registration_copy = models.ImageField(
        upload_to=f"clients/kyc_docs/{user.primary_key}",
        blank=True,
        null=True
    )

    # -----------------------
    # 4) وضعیت KYC
    # -----------------------
    kyc_status = models.CharField(
        max_length=20, choices=KYCStatus.choices, default=KYCStatus.PENDING
    )
    kyc_reject_reason = models.TextField(blank=True, null=True)
    kyc_updated_at = models.DateTimeField(default=timezone.now)

    # متریال تبلیغاتی اصلی (حداقلی)
    primary_ad_image = models.ImageField(upload_to="clients/ads/primary_images/", blank=True, null=True)
    primary_ad_banner = models.ImageField(upload_to="clients/ads/primary_banners/", blank=True, null=True)

    # برای داشتن یک توضیح/سیاست یا متن درخواست تبلیغ
    advertising_description = models.TextField(blank=True, null=True)

    #  «مجوز تبلیغاتی»
    advertising_license_copy = models.ImageField(
        upload_to="clients/ads/licenses/",
        blank=True,
        null=True
    )
    # -----------------------
    # 6) وضعیت فعالیت تبلیغاتی
    # -----------------------
    is_advertising_active = models.BooleanField(default=False)

    # -----------------------
    # 7) زمان‌ها
    # -----------------------
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.advertiser_type == self.AdvertiserType.REAL:
            return f"Client (Real) - {self.full_name or self.user.phone}"
        return f"Client (Legal) - {self.company_name or self.user.phone}"