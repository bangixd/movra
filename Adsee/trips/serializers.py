from rest_framework import serializers
from .models import Trip
from campaigns.models import Campaign
from vehicles.models import Vehicle
from django.utils import timezone


class TripCreateSerializer(serializers.ModelSerializer):
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())
    vehicle = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.all())

    class Meta:
        model = Trip
        fields = ['campaign', 'vehicle']

    def validate_campaign(self, campaign):
        user = self.context['request'].user
        now = timezone.now()
        if campaign.status != 'PUBLISHED':
            raise serializers.ValidationError("این کمپین در حال حاضر فعال نیست.")
        if campaign.start_date and campaign.start_date > now:
            raise serializers.ValidationError("کمپین هنوز شروع نشده است.")
        if campaign.end_date and campaign.end_date < now:
            raise serializers.ValidationError("کمپین به پایان رسیده است.")
        # چک ظرفیت
        active_count = Trip.objects.filter(
            campaign=campaign
        ).exclude(status__in=[Trip.Status.COMPLETED, Trip.Status.CANCELLED]).count()
        if campaign.max_drivers and active_count >= campaign.max_drivers:
            raise serializers.ValidationError("ظرفیت راننده‌های این کمپین تکمیل شده است.")
        return campaign

    def validate_vehicle(self, vehicle):
        user = self.context['request'].user
        if vehicle.driver != user:
            raise serializers.ValidationError("این خودرو متعلق به شما نیست.")
        return vehicle

    def create(self, validated_data):
        validated_data['driver'] = self.context['request'].user
        return super().create(validated_data)


class TripStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = []  # هیچ فیلدی لازم نیست، فقط اکشن

    def update(self, instance, validated_data):
        # این متد در ویوهای اکشن‌ها اورراید می‌شود
        return instance


class TripListSerializer(serializers.ModelSerializer):
    campaign_title = serializers.CharField(source='campaign.title', read_only=True)
    vehicle_plate = serializers.CharField(source='vehicle.plate_number', read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'campaign', 'campaign_title', 'vehicle', 'vehicle_plate',
            'status', 'start_time', 'end_time', 'earnings', 'created_at'
        ]
        read_only_fields = fields


class TripDetailSerializer(serializers.ModelSerializer):
    campaign_title = serializers.CharField(source='campaign.title', read_only=True)
    vehicle_plate = serializers.CharField(source='vehicle.plate_number', read_only=True)
    vehicle_type = serializers.CharField(source='vehicle.vehicle_type.name', read_only=True)
    hourly_rate = serializers.DecimalField(source='vehicle.hourly_rate', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ['driver', 'snapshot', 'created_at', 'updated_at']