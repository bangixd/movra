from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings
from django.contrib.gis.db import models as geomodels

class ClientProfile(models.Model):
    class AdvertiserType(models.TextChoices):
        REAL = "REAL", "حقیقی"
        LEGAL = "LEGAL", "حقوقی"

    class KYCStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    class KYCStep(models.IntegerChoices):
        SELECT_TYPE = 1, "انتخاب نوع فعالیت"
        UPLOAD_DOCUMENTS = 2, "بارگذاری مدارک"
        VERIFICATION = 3, "در انتظار تأیید"
        APPROVED = 4, "تأیید شده"
        REJECTED = 5, "رد شده"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_profile"
    )

    # نوع تبلیغ‌دهنده
    advertiser_type = models.CharField(max_length=10, choices=AdvertiserType.choices, default=AdvertiserType.REAL)
    kyc_step = models.PositiveSmallIntegerField(choices=KYCStep.choices, default=KYCStep.SELECT_TYPE)

    location = geomodels.PointField(srid=4326, null=True, blank=True, verbose_name="موقعیت مکانی")
    # اطلاعات هویتی - حقیقی
    full_name = models.CharField(max_length=120, blank=True, null=True)
    national_id = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r"^\d{10}$", message="کد ملی باید ۱۰ رقمی باشد.")],
        help_text="برای حقیقی: کد ملی ۱۰ رقمی"
    )

    # اطلاعات هویتی - حقوقی
    company_name = models.CharField(max_length=150, blank=True, null=True)
    national_economic_code = models.CharField(max_length=15, blank=True, null=True)
    registration_number = models.CharField(max_length=50, blank=True, null=True)

    # تصویر پروفایل (اختیاری)
    avatar = models.ImageField(upload_to="clients/avatars/", blank=True, null=True)

    # وضعیت احراز هویت (توسط سیگنال به‌روز می‌شود)
    kyc_status = models.CharField(
        max_length=20, choices=KYCStatus.choices, default=KYCStatus.PENDING
    )
    kyc_reject_reason = models.TextField(blank=True, null=True)
    kyc_updated_at = models.DateTimeField(default=timezone.now)

    # وضعیت فعالیت تبلیغاتی (می‌تواند بعداً توسط ادمین یا خودکار تغییر کند)
    is_advertising_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.advertiser_type == self.AdvertiserType.REAL:
            return f"Client (Real) - {self.full_name or self.user.phone}"
        return f"Client (Legal) - {self.company_name or self.user.phone}"