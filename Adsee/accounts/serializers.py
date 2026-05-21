from rest_framework import serializers
from .models import OTP
from django.core.validators import RegexValidator


# =========================
# USER
# =========================
from django.contrib.auth import get_user_model
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "role",
            "is_active",
            "is_staff",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "phone",
            "is_staff",
            "created_at",
            "is_active",
            "role",
        ]

# =========================
# CLIENT
# =========================


# =========================
# OTP
# =========================


class OTPRequestSerializer(serializers.Serializer):

    identifier = serializers.CharField(max_length=11)
    purpose = serializers.ChoiceField(choices=OTP.Purpose.choices, default=OTP.Purpose.LOGIN)

    def validate_identifier(self, value):
        """
        اعتبارسنجی فرمت شماره موبایل: ۱۱ رقم و شروع با 09
        """
        phone_regex = RegexValidator(
            regex=r'^09\d{9}$',
            message="شماره موبایل باید ۱۱ رقمی بوده و با '09' شروع شود.",
            code='invalid_phone_number'
        )
        phone_regex(value)
        return value


class OTPVerifySerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=11)
    otp = serializers.CharField(max_length=6)

    def validate_identifier(self, value: str) -> str:
        value = value.strip()
        if not value.isdigit():
            raise serializers.ValidationError("Phone/identifier must contain only digits.")
        if len(value) != 11:
            raise serializers.ValidationError("Phone/identifier must be exactly 11 digits.")
        return value

    def validate_otp(self, value: str) -> str:
        value = value.strip()
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        if len(value) != 6:
            raise serializers.ValidationError("OTP must be exactly 6 digits.")
        return value


class OTPSerializer(serializers.ModelSerializer):
    """
    اگر نیاز داشتید می‌توانید استفاده کنید (مثلاً در پنل ادمین).
    """
    used = serializers.BooleanField(read_only=True)
    used_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = OTP
        fields = [
            "id",
            "identifier",
            "purpose",
            "code",
            "created_at",
            "expires_at",
            "used_at",
            "used",
            "user",
        ]
        read_only_fields = fields


# =========================
# Optional: serializer selector helper
# =========================

