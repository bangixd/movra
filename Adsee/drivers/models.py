from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import User
from django.core.validators import RegexValidator


class DriverProfile(models.Model):
    # وضعیت‌های ثبت‌نام
    class RegistrationStep(models.IntegerChoices):
        PERSONAL_INFO = 1, 'اطلاعات شخصی'
        DOCUMENTS = 2, 'بارگذاری مدارک'
        VERIFICATION = 3, 'احراز هویت'
        CONTRACT = 4, 'قرارداد'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )

    # اطلاعات مرحله ۱
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    national_id = models.CharField(max_length=10, unique=True, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    city = models.ForeignKey(
        'geo.City',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='drivers'
    )

    # اطلاعات تکمیلی (اختیاری)
    avatar = models.ImageField(upload_to='drivers/avatars/', blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('MALE', 'مرد'), ('FEMALE', 'زن')], blank=True, null=True)
    father_name = models.CharField(max_length=100, blank=True, null=True)

    # وضعیت احراز هویت (مرحله ۳)
    kyc_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'در انتظار'),
            ('APPROVED', 'تأیید شده'),
            ('REJECTED', 'رد شده'),
        ],
        default='PENDING'
    )
    kyc_submitted_at = models.DateTimeField(blank=True, null=True)
    kyc_reviewed_at = models.DateTimeField(blank=True, null=True)
    kyc_reject_reason = models.TextField(blank=True, null=True)

    # مرحله ثبت‌نام جاری
    registration_step = models.PositiveSmallIntegerField(
        choices=RegistrationStep.choices,
        default=RegistrationStep.PERSONAL_INFO
    )
    # مرحله ۴: پذیرش قرارداد
    is_contract_accepted = models.BooleanField(default=False)

    # تنظیمات موقعیت (اختیاری)
    share_location = models.BooleanField(default=True)
    last_location_update = models.DateTimeField(blank=True, null=True)

    #کد دعوت راننده
    referral_code = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name="کد معرف")
    referred_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='referrals',
        verbose_name="دعوت‌شده توسط"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.user.phone

    def __str__(self):
        return f"Driver: {self.full_name}"

    class Meta:
        verbose_name = 'پروفایل راننده'
        verbose_name_plural = 'پروفایل رانندگان'

class DriverDocument(models.Model):
    class DocumentType(models.TextChoices):
        PROFILE_PICTURE = 'PROFILE_PICTURE', 'عکس پروفایل'
        DRIVING_LICENSE = 'DRIVING_LICENSE', 'گواهینامه'
        VEHICLE_CARD = 'VEHICLE_CARD', 'کارت خودرو'
        GREEN_SHEET = 'GREEN_SHEET', 'برگه سبز'

    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار'
        APPROVED = 'APPROVED', 'تأیید شده'
        REJECTED = 'REJECTED', 'رد شده'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='driver_documents')
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file = models.FileField(upload_to='drivers/documents/')
    status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.phone} - {self.document_type}"