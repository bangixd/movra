from django.db import models
from accounts.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings


class ClientProfile(models.Model):
    class AdvertiserType(models.TextChoices):
        REAL = "REAL", "Real"
        LEGAL = "LEGAL", "Legal"

    class KYCStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_profile"
    )

    # نوع تبلیغ‌دهنده
    advertiser_type = models.CharField(
        max_length=10, choices=AdvertiserType.choices, default=AdvertiserType.REAL
    )

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

class ClientDocument(models.Model):
    class DocumentType(models.TextChoices):
        NATIONAL_ID = 'NATIONAL_ID', 'National ID'
        COMPANY_REGISTRATION = 'COMPANY_REGISTRATION', 'Company Registration'
        ADVERTISING_LICENSE = 'ADVERTISING_LICENSE', 'Advertising License'
        TAX_CERTIFICATE = 'TAX_CERTIFICATE', 'Tax Certificate'
        OTHER = 'OTHER', 'Other'

    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_documents')
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file = models.FileField(upload_to='clients/documents/')
    status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.phone} - {self.document_type}"