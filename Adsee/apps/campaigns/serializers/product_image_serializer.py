from rest_framework import serializers
from campaigns.models import ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = [
            'id',
            'campaign_design',
            'image',
        ]
        read_only_fields = ['id']
