from rest_framework import serializers
from campaigns.models import Campaign

class AvailableCampaignSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand_name.name', read_only=True)
    banner_type = serializers.CharField(source='design.design_type', read_only=True)
    delivery_address = serializers.SerializerMethodField()
    amount = serializers.DecimalField(
        source='cost.total_price',
        read_only=True,
        max_digits=14,
        decimal_places=2
    )
    class Meta:
        model = Campaign
        fields = [
            'id', 'brand_name', 'banner_type', 'delivery_address',
            'start_date', 'end_date', 'description', 'amount',
            'slogan'
        ]

    def get_delivery_address(self, obj):
        # آدرس چاپخانه‌ای که طرح به آن ارجاع شده است
        design = getattr(obj, 'design', None)
        if design and design.print_shop:
            return design.print_shop.address
        return None
