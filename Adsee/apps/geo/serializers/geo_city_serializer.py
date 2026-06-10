from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers
from geo.models import City
from geo.serializers import ProvinceSerializer


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
