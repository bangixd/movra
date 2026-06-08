from rest_framework import serializers
from campaigns.models import ProductImage


class ProductImageNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']
