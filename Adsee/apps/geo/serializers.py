from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers
from .models import Province, City, Neighborhood, SuggestedRoute, DriverLocation


# ---------- Province ----------
class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'name']


# ---------- City ----------
class CitySerializer(serializers.ModelSerializer):
    province_detail = ProvinceSerializer(source='province', read_only=True)
    center = gis_serializers.GeometryField(precision=6)  # مختصات با ۶ رقم اعشار

    class Meta:
        model = City
        fields = ['id', 'province', 'province_detail', 'name', 'center']

    def create(self, validated_data):
        # center رو که GeometryField برگردونده، مستقیماً استفاده می‌کنیم
        return super().create(validated_data)


# برای نمایش لیست (بدون مختصات کامل) می‌تونیم یه سریالایزر خلاصه هم داشته باشیم
class CityListSerializer(serializers.ModelSerializer):
    province_name = serializers.CharField(source='province.name', read_only=True)

    class Meta:
        model = City
        fields = ['id', 'province_name', 'name']


# ---------- Neighborhood ----------
class NeighborhoodSerializer(serializers.ModelSerializer):
    city_detail = CityListSerializer(source='city', read_only=True)
    center = gis_serializers.GeometryField(precision=6)

    class Meta:
        model = Neighborhood
        fields = [
            'id', 'city', 'city_detail', 'name',
            'center', 'radius_meter'
        ]


# ---------- SuggestedRoute ----------
class SuggestedRouteSerializer(serializers.ModelSerializer):
    city_detail = CityListSerializer(source='city', read_only=True)
    path = gis_serializers.GeometryField(precision=6)

    class Meta:
        model = SuggestedRoute
        fields = ['id', 'city', 'city_detail', 'name', 'description', 'path']


# ---------- DriverLocation ----------
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


class BatchLocationSerializer(serializers.Serializer):
    trip_id = serializers.IntegerField(required=True)
    points = serializers.ListField(
        child=serializers.DictField(
            child=serializers.FloatField(),
            allow_empty=False
        ),
        allow_empty=False,
        help_text="لیست نقاط به فرمت [{'lat':..., 'lon':..., 'timestamp':..., 'speed':..., 'heading':...}, ...]"
    )