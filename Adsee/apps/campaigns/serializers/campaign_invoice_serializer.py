from rest_framework import serializers
from campaigns.models import CampaignInvoice
class CampaignInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignInvoice
        fields = [
            'id', 'campaign',
            'invoice_number', 'status',
            'subtotal_price', 'discount_amount', 'tax_amount', 'total_price',
            'expires_at', 'paid_at',
            'snapshot',
            'modification_type', 'modification_data',
            'created_at'
        ]
        read_only_fields = [
            'campaign', 'invoice_number', 'status',
            'subtotal_price', 'discount_amount', 'tax_amount', 'total_price',
            'snapshot', 'created_at',
            'modification_type', 'modification_data'
        ]
