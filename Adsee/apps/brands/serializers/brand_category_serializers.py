from rest_framework import serializers
from brands.models import BrandCategory

class BrandCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandCategory
        fields = ['id', 'name']

class AdminBrandCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandCategory
        fields = ['id', 'name', 'is_active']