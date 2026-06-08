from rest_framework import serializers
from campaigns.models import Campaign

class CampaignBriefSerializer(serializers.ModelSerializer):
    """برای نمایش خلاصه کمپین در لیست راننده"""
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    area_type = serializers.CharField(source='area.area_type', read_only=True)
    max_driver = serializers.CharField(source='campaignsetting.max_driver', read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'slogan', 'brand_name', 'area_type',
            'start_date', 'end_date', 'max_driver'
        ]
