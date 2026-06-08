from rest_framework import serializers
from brands.models import Brand

class BrandMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']
