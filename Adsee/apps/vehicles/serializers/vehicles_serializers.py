from rest_framework import serializers
from vehicles.models import VehicleType, Vehicle


# ---- VehicleType ----
class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ['id', 'name', 'description', 'base_hourly_rate', 'is_active']
        # ادمین می‌تونه base_hourly_rate رو عوض کنه، پس read_only نمی‌ذاریم


# ---- Vehicle ----
class VehicleListSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    vehicle_type_name = serializers.CharField(source='vehicle_type.name', read_only=True)
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'plate_number', 'vehicle_type', 'vehicle_type_name',
            'driver_name', 'hourly_rate', 'banner_max_width_cm',
            'banner_max_height_cm', 'is_active'
        ]


class VehicleDetailSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    vehicle_type_detail = VehicleTypeSerializer(source='vehicle_type', read_only=True)
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ['driver', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['driver'] = self.context['request'].user.driver_profile
        return super().create(validated_data)