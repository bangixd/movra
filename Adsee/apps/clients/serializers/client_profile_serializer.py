from clients.models import ClientProfile
from rest_framework import serializers
from campaigns.models import Campaign

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