from rest_framework import serializers
from geo.models import City, Neighborhood, SuggestedRoute

class CityMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name"]
