from rest_framework import serializers
from .models import Brand, BrandCategory
from trips.models import TripAnalysis
from campaigns.models import Campaign
from django.db.models import Sum
from django.utils import timezone


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

class BrandCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandCategory
        fields = ['id', 'name']

class BrandListSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    active_campaigns_count = serializers.SerializerMethodField()
    total_impressions = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'logo', 'city_name', 'category_name', 'status',
            'active_campaigns_count', 'total_impressions', 'remaining_days',
            'phone', 'whatsapp', 'telegram', 'website'
        ]

    def get_active_campaigns_count(self, obj):
        return obj.campaigns.filter(status__in=[Campaign.Status.ACTIVE, Campaign.Status.PAUSED]).count()

    def get_total_impressions(self, obj):
        total = TripAnalysis.objects.filter(
            trip__campaign__brand_name=obj
        ).aggregate(Sum('estimated_impressions'))['estimated_impressions__sum'] or 0
        return total

    def get_remaining_days(self, obj):
        today = timezone.now().date()
        remaining = 0
        for campaign in obj.campaigns.filter(status__in=[Campaign.Status.ACTIVE, Campaign.Status.PAUSED], end_date__gte=today):
            remaining += (campaign.end_date - today).days
        return remaining

class BrandCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            'name', 'slug', 'logo', 'description',
            'city', 'category', 'phone', 'website',
            'whatsapp', 'telegram'
        ]

    def create(self, validated_data):
        validated_data['client'] = self.context['request'].user.client_profile
        validated_data['status'] = 'PENDING'
        return super().create(validated_data)