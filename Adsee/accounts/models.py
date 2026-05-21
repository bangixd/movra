from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.db import models
from django.conf import settings


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
        PRINT_SHOP = "PRINT_SHOP", "Print Shop"

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
