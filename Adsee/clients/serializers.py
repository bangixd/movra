from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import ClientProfile, ClientDocument
from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

class ClientLocationSerializer(serializers.Serializer):
    lat = serializers.FloatField(required=True)
    lng = serializers.FloatField(required=True)

class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = [
            'id', 'user', 'advertiser_type',
            'full_name', 'national_id',
            'company_name', 'national_economic_code', 'registration_number',
            'avatar',
            'kyc_status', 'kyc_reject_reason', 'kyc_updated_at',
            'is_advertising_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'kyc_status', 'kyc_updated_at', 'created_at', 'updated_at']

class ClientDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientDocument
        fields = ['id', 'user', 'document_type', 'file', 'status', 'submitted_at', 'reviewed_at', 'reject_reason']
        read_only_fields = ['user', 'status', 'submitted_at', 'reviewed_at', 'reject_reason']