from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers
from geo.models import SuggestedRoute
from geo.serializers import CityListSerializer

class SuggestedRouteSerializer(serializers.ModelSerializer):
    city_detail = CityListSerializer(source='city', read_only=True)
    path = gis_serializers.GeometryField(precision=6)

    class Meta:
        model = SuggestedRoute
        fields = ['id', 'city', 'city_detail', 'name', 'description', 'path']
