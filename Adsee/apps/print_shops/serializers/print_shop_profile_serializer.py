from rest_framework import serializers
from print_shops.models import PrintShopProfile

class PrintShopProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintShopProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']