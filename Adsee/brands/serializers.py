from rest_framework import serializers
from .models import Brand


class BrandListSerializer(serializers.ModelSerializer):
    """برای نمایش لیست برندها (خلاصه)"""
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'phone', 'is_active']


class BrandDetailSerializer(serializers.ModelSerializer):
    """جزئیات کامل یک برند"""
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ['client', 'slug', 'created_at', 'updated_at']

    def create(self, validated_data):
        # کلاینت از کاربر لاگین‌شده پر می‌شود
        validated_data['client'] = self.context['request'].user.client_profile
        return super().create(validated_data)