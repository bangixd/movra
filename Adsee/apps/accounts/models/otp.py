from django.utils import timezone
from django.db import models
from django.conf import settings

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
        app_label = 'accounts'
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