from rest_framework import serializers
from campaigns.models import CampaignPricingRule

class PricingRuleAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignPricingRule
        fields = ['id', 'key', 'title', 'value_type', 'decimal_value', 'integer_value',
                  'boolean_value', 'text_value', 'json_value', 'is_active']
        read_only_fields = ['key']  # کلید نباید تغییر کند
