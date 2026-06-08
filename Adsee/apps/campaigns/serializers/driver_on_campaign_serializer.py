from rest_framework import serializers
from geo.models import DriverLocation
class DriverOnCampaignSerializer(serializers.Serializer):
    driver_id = serializers.IntegerField(source='driver.id')
    driver_name = serializers.CharField(source='driver.full_name')
    driver_avatar = serializers.ImageField(source='driver.avatar')
    car_model = serializers.CharField(source='vehicle.vehicle_model')
    sticker_image = serializers.ImageField()  # از Trip
    driver_car_image = serializers.ImageField()
    trip_status = serializers.CharField(source='status')
    active_seconds = serializers.SerializerMethodField()
    last_location = serializers.SerializerMethodField()
    zone_name = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(source='driver.average_rating')
    total_ratings = serializers.IntegerField(source='driver.total_ratings')

    def get_active_seconds(self, obj):
        # obj یک Trip است
        if hasattr(obj, 'analysis') and obj.analysis:
            return obj.analysis.active_seconds
        return 0

    def get_last_location(self, obj):
        last_loc = DriverLocation.objects.filter(trip=obj).order_by('-timestamp').first()
        if last_loc:
            return {
                'lat': last_loc.point.y,
                'lng': last_loc.point.x,
                'timestamp': last_loc.timestamp.isoformat()
            }
        return None

    def get_zone_name(self, obj):
        area = obj.campaign.area
        if area and area.city:
            return area.city.name
        return None

    def get_rating(self, obj):
        # می‌توان یک امتیاز فرضی یا میانگین exposure برگرداند
        return 0.0
