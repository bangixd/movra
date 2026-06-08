from rest_framework import serializers
from campaigns.models import CampaignInvoice
class CampaignInvoiceReadSerializer(serializers.ModelSerializer):
    campaign_title = serializers.CharField(source='campaign.title', read_only=True)
    client_name = serializers.SerializerMethodField()
    campaign_cost_summary = serializers.SerializerMethodField()

    class Meta:
        model = CampaignInvoice
        fields = [
            'id', 'campaign', 'campaign_title', 'client_name',
            'campaign_cost_summary',
            'invoice_number', 'status',
            'subtotal_price', 'discount_amount', 'tax_amount', 'total_price',
            'expires_at', 'paid_at', 'snapshot', 'created_at'
        ]
        read_only_fields = fields  # کلاً read-only، چون این فقط برای نمایشه

    def get_client_name(self, obj):
        # فرض: هر campaign یه brand داره، هر brand یه client داره
        return obj.campaign.brand.client.get_full_name()

    def get_campaign_cost_summary(self, obj):
        # می‌تونی خلاصه‌ای از campaign_cost برگردونی
        # ولی چون snapshot داری، شاید لازم نباشه
        return {
            "subtotal": str(obj.subtotal_price),
            "discount": str(obj.discount_amount),
            "tax": str(obj.tax_amount),
            "total": str(obj.total_price)
        }
