from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers
from geo.models import Neighborhood
from geo.serializers import CityListSerializer

class NeighborhoodSerializer(serializers.ModelSerializer):
    city_detail = CityListSerializer(source='city', read_only=True)
    center = gis_serializers.GeometryField(precision=6)

    class Meta:
        model = Neighborhood
        fields = [
            'id', 'city', 'city_detail', 'name',
            'center', 'radius_meter'
        ]
