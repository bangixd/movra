from rest_framework import serializers
from .models import DriverProfile, DriverDocument


class DriverProfileSerializer(serializers.ModelSerializer):

    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = DriverProfile
        fields = [
            'user', # یا 'user_id' اگر فقط id کاربر را می‌خواهید
            'full_name',
            'national_id',
            'birth_date',
            'gender',
            'avatar', # فیلد اصلی برای آپلود
            'avatar_url', # URL تصویر برای نمایش
            'father_name',
            'kyc_status',
            'kyc_reject_reason',
            'kyc_submitted_at',
            'kyc_reviewed_at',
            'vehicle_type',
            'share_location',
            'last_location_update',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'kyc_reviewed_at', 'last_location_update', 'created_at', 'updated_at'] # فیلدهایی که نباید در فرم ویرایش شوند یا توسط سیستم پر می شوند

    # --- متدهای کمکی برای تولید URL تصاویر ---

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


    # --- متد clean برای اعتبارسنجی‌های شرطی ---
    def clean(self):
        cleaned_data = super().clean()
        national_id = cleaned_data.get('national_id')
        # license_image = cleaned_data.get('license_image')
        # vehicle_registration_copy = cleaned_data.get('vehicle_registration_copy')
        kyc_status = cleaned_data.get('kyc_status')
        kyc_reject_reason = cleaned_data.get('kyc_reject_reason')

        # اعتبارسنجی کد ملی (اگر اجباری باشد)
        if national_id and len(national_id) != 10:
            raise serializers.ValidationError({"national_id": "کد ملی باید ۱۰ رقمی باشد."})

        # اعتبارسنجی دلیل رد شدن KYC
        if kyc_status == 'REJECTED':  # فرض می‌کنیم مقدار 'REJECTED' است
            if not kyc_reject_reason:
                raise serializers.ValidationError({"kyc_reject_reason": "دلیل رد شدن KYC الزامی است."})

        return cleaned_data

    # def create(self, validated_data):
    #     user_data = validated_data.pop('user') # اگر user را هم در فرم قرار داده اید
    #     user = User.objects.create_user(**user_data)
    #     driver_profile = DriverProfile.objects.create(user=user, **validated_data)
    #     return driver_profile

    # def update(self, instance, validated_data):
    #     user_data = validated_data.pop('user', None)
    #     if user_data:
    #         user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
    #         user_serializer.is_valid(raise_exception=True)
    #         user_serializer.save()
    #     return super().update(instance, validated_data)


class DriverDocumentSerializer(serializers.ModelSerializer):
    """
    برای نمایش و دریافت اطلاعات مدارک.
    """
    class Meta:
        model = DriverDocument
        fields = [
            "id",
            "document_type",
            "file",
            "status",
            "submitted_at",
            "reviewed_at",
            "reject_reason",
        ]
        read_only_fields = ["status", "submitted_at", "reviewed_at", "reject_reason"]


class DriverProfileKycUpdateSerializer(serializers.ModelSerializer):
    """
    برای به‌روزرسانی وضعیت کلی KYC در DriverProfile.
    """
    class Meta:
        model = DriverProfile
        fields = [
            "kyc_status",
            "kyc_reject_reason",
            "kyc_submitted_at", # این فیلد در view تنظیم میشه
            "kyc_reviewed_at",  # این فیلد در view تنظیم میشه
        ]
        read_only_fields = [
            "kyc_status",
            "kyc_reject_reason",
            "kyc_reviewed_at",
        ]


class DriverProfileKycStatusSerializer(serializers.ModelSerializer):
    """
    برای نمایش وضعیت کلی KYC و جزئیات مدارک.
    """
    documents = DriverDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = DriverProfile
        fields = [
            "kyc_status",
            "kyc_reject_reason",
            "kyc_submitted_at",
            "kyc_reviewed_at",
            "documents",
        ]
