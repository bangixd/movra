from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers
from geo.models import DriverLocation

# برای نوشتن (POST) – فقط مختصات را از راننده می‌گیریم
class DriverLocationCreateSerializer(serializers.ModelSerializer):
    point = gis_serializers.GeometryField(precision=6)

    class Meta:
        model = DriverLocation
        fields = ['point']  # driver و trip در view پر می‌شوند

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['driver'] = request.user
        # اگر trip فعالی وجود داشته باشد، می‌توان آن را هم اضافه کرد
        # validated_data['trip'] = get_active_trip(request.user)
        return super().create(validated_data)


# برای نمایش (Read) – با جزئیات راننده و سفر
class DriverLocationReadSerializer(serializers.ModelSerializer):
    point = gis_serializers.GeometryField(precision=6)
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)

    class Meta:
        model = DriverLocation
        fields = ['id', 'driver', 'driver_name', 'trip', 'point', 'timestamp']
        read_only_fields = fields
