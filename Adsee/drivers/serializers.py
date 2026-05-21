from rest_framework import serializers
from .models import DriverProfile, DriverDocument


class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = [
            'id', 'user',
            'full_name', 'national_id', 'birth_date', 'gender', 'avatar', 'father_name',
            'kyc_status', 'kyc_submitted_at', 'kyc_reviewed_at', 'kyc_reject_reason',
            'share_location', 'last_location_update',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'kyc_status', 'kyc_submitted_at', 'kyc_reviewed_at', 'created_at', 'updated_at']

class DriverDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverDocument
        fields = ['id', 'user', 'document_type', 'file', 'status', 'submitted_at', 'reviewed_at', 'reject_reason']
        read_only_fields = ['user', 'status', 'submitted_at', 'reviewed_at', 'reject_reason']
