from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import ClientProfile, ClientDocument
from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers
from campaigns.models import Campaign


class ClientLocationSerializer(serializers.Serializer):
    lat = serializers.FloatField(required=True)
    lng = serializers.FloatField(required=True)

class ClientProfileSerializer(serializers.ModelSerializer):
    wallet_balance = serializers.DecimalField(source='user.wallet.balance', max_digits=12, decimal_places=2, read_only=True)
    active_campaigns_count = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = '__all__'  # یا لیست صریح شامل wallet_balance, active_campaigns_count
        # اگر از '__all__' استفاده می‌کنید، این دو فیلد هم خودکار اضافه می‌شوند.

    def get_active_campaigns_count(self, obj):
        return Campaign.objects.filter(
            brand_name__client=obj,
            status__in=[Campaign.Status.ACTIVE, Campaign.Status.PAUSED]
        ).count()

class ClientDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientDocument
        fields = ['id', 'user', 'document_type', 'file', 'status', 'submitted_at', 'reviewed_at', 'reject_reason']
        read_only_fields = ['user', 'status', 'submitted_at', 'reviewed_at', 'reject_reason']