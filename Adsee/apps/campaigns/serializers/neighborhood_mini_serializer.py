from rest_framework import serializers
from geo.models import City, Neighborhood, SuggestedRoute

class NeighborhoodMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Neighborhood
        fields = ["id", "name", "city"]
