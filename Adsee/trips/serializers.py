from rest_framework import serializers
from .models import Trip, TripAnalysis
from campaigns.models import Campaign
from vehicles.models import Vehicle
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError



class TripCreateSerializer(serializers.ModelSerializer):
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())
    vehicle = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.all())

    class Meta:
        model = Trip
        fields = ['id', 'campaign', 'vehicle']

    def validate_campaign(self, campaign):
        user = self.context['request'].user
        now = timezone.now()
        if campaign.status != Campaign.Status.ACTIVE:
            raise serializers.ValidationError("این کمپین در حال حاضر فعال نیست.")
        if campaign.created_at and campaign.created_at > now:
            raise serializers.ValidationError("کمپین هنوز شروع نشده است.")
        # if campaign.end_date and campaign.end_date < now:
        #     raise serializers.ValidationError("کمپین به پایان رسیده است.")
        # چک ظرفیت
        active_count = Trip.objects.filter(
            campaign=campaign
        ).exclude(status__in=[Trip.Status.COMPLETED, Trip.Status.CANCELLED]).count()
        if campaign.setting.max_driver and active_count >= campaign.setting.max_driver:
            raise serializers.ValidationError("ظرفیت راننده‌های این کمپین تکمیل شده است.")
        return campaign

    def validate_vehicle(self, vehicle):
        user = self.context['request'].user
        if vehicle.driver != user.driver_profile:
            raise serializers.ValidationError("این خودرو متعلق به شما نیست.")
        return vehicle

    def create(self, validated_data):
        validated_data['driver'] = self.context['request'].user.driver_profile
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)


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
    print_shop_name = serializers.CharField(
        source='campaign.design.print_shop.shop_name',
        read_only=True, allow_null=True
    )
    print_shop_address = serializers.CharField(
        source='campaign.design.print_shop.address',
        read_only=True, allow_null=True
    )
    print_shop_phone = serializers.CharField(
        source='campaign.design.print_shop.phone',
        read_only=True, allow_null=True
    )


    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ['driver', 'snapshot', 'created_at', 'updated_at',
                            'print_shop_name', 'print_shop_address', 'print_shop_phone',]

class TripAnalysisSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='trip.driver.full_name', read_only=True)
    vehicle_plate = serializers.CharField(source='trip.vehicle.plate_number', read_only=True)
    campaign_title = serializers.CharField(source='trip.campaign.slogan', read_only=True)

    class Meta:
        model = TripAnalysis
        fields = '__all__'