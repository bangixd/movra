from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from utils import upload_document_path


class UserManager(BaseUserManager):
    def create_user(self, phone, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")

        user = self.model(phone=phone, **extra_fields)

        # مهم: پسورد غیرقابل استفاده
        user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if not password:
            raise ValueError("Superuser must have a password.")

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)  # ✅ فقط سوپریوزر پسورد دارد
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CLIENT = "CLIENT", "Client"
        DRIVER = "DRIVER", "Driver"

    phone = models.CharField(max_length=11, unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone

# DRIVER


class DriverProfile(models.Model):

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="driver_profile"
    )

    # ---------- اطلاعات هویتی ----------
    full_name = models.CharField(max_length=100)
    national_id = models.CharField(max_length=10)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10, choices=[("MALE", "مرد"), ("FEMALE", "زن")], blank=True, null=True
    )
    avatar = models.ImageField(upload_to="drivers/avatars/", blank=True, null=True)
    father_name = models.CharField(max_length=100, blank=True, null=True)

    # ---------- وضعیت احراز هویت ----------
    kyc_status = models.CharField(
        max_length=20,
        choices=[
            ("NOT_STARTED", "Not Started"),
            ("PENDING", "Pending"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
        ],
        default="NOT_STARTED",
    )
    kyc_submitted_at = models.DateTimeField(blank=True, null=True)
    kyc_reviewed_at = models.DateTimeField(blank=True, null=True)
    kyc_reject_reason = models.TextField(blank=True, null=True)

    # ---------- اطلاعات خودرو ----------
    # vehicle_model = models.CharField(max_length=100, blank=True, null=True)
    # vehicle_year = models.CharField(max_length=4, blank=True, null=True)
    # vehicle_color = models.CharField(max_length=50, blank=True, null=True)
    # vehicle_plate = models.CharField(max_length=20, blank=True, null=True)
    # vehicle_plate_image = models.ImageField(upload_to="drivers/plates/", blank=True, null=True)
    # license_number = models.CharField(max_length=20, blank=True, null=True)
    vehicle_type = models.ForeignKey(
        "vehicles.VehicleType",
        on_delete=models.PROTECT,
        related_name="drivers",
        null=True,
        blank=True
    )

    # ---------- موقعیت و تنظیمات موقعیت ----------
    share_location = models.BooleanField(default=True)
    last_location_update = models.DateTimeField(blank=True, null=True)

    # ---------- زمان ایجاد ----------
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DriverProfile for {self.user.phone}"

    class Meta:
        verbose_name = "پروفایل راننده"
        verbose_name_plural = "پروفایل رانندگان"


class DriverDocument(models.Model):

    class DocumentType(models.TextChoices):
        NATIONAL_ID_FRONT = "NATIONAL_ID_FRONT", "National ID Front"
        NATIONAL_ID_BACK = "NATIONAL_ID_BACK", "National ID Back"
        DRIVING_LICENSE = "DRIVING_LICENSE", "Driving License"
        VEHICLE_REGISTRATION = "VEHICLE_REGISTRATION", "Vehicle Registration"

    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DocumentType.choices)
    file = models.ImageField(upload_to=upload_document_path, blank=True, null=True)
    status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reject_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.document_type} - {self.user.username} - {self.status}"

# CLIENT


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


# KYC

#
# class KycVerificationRequest(models.Model):
#     """
#     مدلی برای ردیابی درخواست‌های ارسال شده به سرویس KYC خارجی.
#     """
#     # وضعیت‌های ممکن برای درخواست
#     STATUS_CHOICES = [
#         ('SUBMITTED', 'Submitted'),       # ارسال شده به سرویس خارجی، منتظر بررسی
#         ('PENDING', 'Pending'),           # در حال بررسی توسط سرویس خارجی
#         ('APPROVED', 'Approved'),         # تایید شده توسط سرویس خارجی
#         ('REJECTED', 'Rejected'),         # رد شده توسط سرویس خارجی
#         ('FAILED', 'Failed'),             # خطایی در پردازش یا ارسال رخ داده
#     ]
#
#     driver_profile = models.ForeignKey(
#         'DriverProfile', # نام مدل پروفایل راننده شما
#         on_delete=models.CASCADE,
#         related_name='kyc_requests', # نامی برای دسترسی از پروفایل به درخواست‌ها
#         help_text="پروفایل راننده‌ای که این درخواست KYC برای او ثبت شده."
#     )
#     external_request_id = models.CharField(
#         max_length=255,
#         unique=True, # شناسه سرویس خارجی باید یکتا باشد
#         help_text="شناسه منحصر به فرد درخواست در سرویس KYC خارجی."
#     )
#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default='SUBMITTED',
#         help_text="وضعیت فعلی درخواست KYC در سیستم خارجی."
#     )
#     reject_reason = models.TextField(
#         blank=True,
#         null=True,
#         help_text="دلیل رد شدن درخواست توسط سرویس خارجی (در صورت رد شدن)."
#     )
#     submitted_at = models.DateTimeField(
#         default=timezone.now,
#         help_text="زمان ثبت اولیه درخواست در سیستم شما."
#     )
#     external_reviewed_at = models.DateTimeField(
#         blank=True,
#         null=True,
#         help_text="زمان نهایی شدن بررسی در سرویس خارجی (در صورت دریافت)."
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         verbose_name = "KYC Verification Request"
#         verbose_name_plural = "KYC Verification Requests"
#         ordering = ['-submitted_at'] # مرتب‌سازی بر اساس جدیدترین درخواست‌ها
#
#     def __str__(self):
#         return f"KYC Request {self.external_request_id} for {self.driver_profile.user.username} - Status: {self.status}"
#
#     # اگر بخواهی تابع کمکی برای بروزرسانی وضعیت کلی DriverProfile اینجا اضافه کنی:
#     def update_driver_profile_status(self):
#         """
#         بروزرسانی وضعیت کلی KYC در DriverProfile بر اساس وضعیت این درخواست.
#         این تابع باید با دقت و در جای مناسب فراخوانی شود.
#         """
#         profile = self.driver_profile
#         if self.status == 'APPROVED':
#             profile.kyc_status = 'APPROVED'
#             profile.kyc_reject_reason = None
#         elif self.status == 'REJECTED':
#             profile.kyc_status = 'REJECTED'
#             profile.kyc_reject_reason = self.reject_reason
#         else: # PENDING, SUBMITTED, FAILED
#             # اگر هنوز پاسخ نهایی نیامده یا پردازش ناموفق بوده، وضعیت را PENDING نگه دار
#             # مگر اینکه بخواهی FAILED را به شکل دیگری مدیریت کنی
#             profile.kyc_status = 'PENDING'
#             profile.kyc_reject_reason = None
#
#         profile.kyc_reviewed_at = self.external_reviewed_at if self.external_reviewed_at else timezone.now()
#         profile.save(update_fields=['kyc_status', 'kyc_reject_reason', 'kyc_reviewed_at'])


# OTP

class OTP(models.Model):
    class Purpose(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        REGISTER = "REGISTER", "Register"
        VERIFY_PROFILE = "VERIFY_PROFILE", "Verify profile step"

    identifier = models.CharField(max_length=11, db_index=True)  # phone
    purpose = models.CharField(max_length=30, choices=Purpose.choices, default=Purpose.LOGIN)

    code = models.CharField(max_length=6)  # مثل '123456' (حتماً string بمونه)
    created_at = models.DateTimeField(auto_now_add=True)

    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    used = models.BooleanField(default=False)

    # اختیاری: اگر OTP مربوط به user مشخصی باشد
    # اگر نقش ساخت/ثبت نام جدید دارید، این فیلد می‌تواند null باشد
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="otps"
    )

    class Meta:
        indexes = [
            models.Index(fields=["identifier", "purpose", "used"]),
        ]
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def mark_used(self):
        self.used = True
        self.used_at = timezone.now()
        self.save(update_fields=["used", "used_at"])

    def __str__(self):
        status = "USED" if self.used else "ACTIVE"
        return f"OTP({self.identifier}, {self.purpose}, {status})"
