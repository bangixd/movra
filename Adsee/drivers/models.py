from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import User
from django.core.validators import RegexValidator
from utils import upload_document_path



class DriverProfile(models.Model):

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="driver_profile"
    )

    # ---------- اطلاعات هویتی ----------
    full_name = models.CharField(max_length=100)
    national_id = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[RegexValidator(r"^\d{10}$", message="کد ملی باید ۱۰ رقمی باشد.")],
        help_text="برای حقیقی: کد ملی ۱۰ رقمی"
    )
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