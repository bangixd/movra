from rest_framework import serializers
from .models import DriverProfile, DriverDocument
from geo.models import City

class DriverProfileSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    province_name = serializers.CharField(source='city.province.name', read_only=True)
    wallet_balance = serializers.DecimalField(
        source='user.wallet.balance',
        read_only=True,
        max_digits=12,
        decimal_places=2
    )

    class Meta:
        model = DriverProfile
        fields = [
            'id', 'user',
            'first_name', 'last_name', 'national_id', 'birth_date',
            'city', 'city_name', 'province_name',
            'avatar', 'gender', 'father_name',
            'kyc_status', 'kyc_reject_reason',
            'registration_step', 'is_contract_accepted',
            'share_location', 'last_location_update',
            'wallet_balance',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'kyc_status', 'registration_step', 'is_contract_accepted', 'created_at', 'updated_at']

    def validate(self, data):
        # در مرحله ۱، فیلدهای اجباری را چک کن
        if self.instance and self.instance.registration_step == DriverProfile.RegistrationStep.PERSONAL_INFO:
            required = ['first_name', 'last_name', 'national_id', 'birth_date', 'city']
            for field in required:
                if field not in data or not data[field]:
                    raise serializers.ValidationError({field: f'{field} الزامی است.'})
        return data

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        # بعد از تکمیل اطلاعات مرحله ۱، گام را به ۲ ببر
        if instance.registration_step == DriverProfile.RegistrationStep.PERSONAL_INFO:
            if all([
                instance.first_name, instance.last_name,
                instance.national_id, instance.birth_date, instance.city
            ]):
                instance.registration_step = DriverProfile.RegistrationStep.DOCUMENTS
                instance.save(update_fields=['registration_step'])
        return instance


class DriverDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverDocument
        fields = ['id', 'user', 'document_type', 'file', 'status', 'submitted_at', 'reviewed_at', 'reject_reason']
        read_only_fields = ['user', 'status', 'submitted_at', 'reviewed_at', 'reject_reason']