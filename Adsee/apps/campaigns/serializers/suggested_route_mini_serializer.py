from rest_framework import serializers
from geo.models import City, Neighborhood, SuggestedRoute

class SuggestedRouteMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuggestedRoute
        fields = ["id", "name"]
