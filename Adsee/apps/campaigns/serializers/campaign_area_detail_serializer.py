from rest_framework import serializers
from campaigns.models import CampaignArea
from campaigns.serializers import CityMiniSerializer, NeighborhoodMiniSerializer,\
    SuggestedRouteMiniSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeometryField

class CampaignAreaDetailSerializer(serializers.ModelSerializer):
    city = CityMiniSerializer(read_only=True)
    neighborhood = NeighborhoodMiniSerializer(read_only=True)
    suggested_route = SuggestedRouteMiniSerializer(read_only=True)

    targeting_geometry = GeometryField(source="get_targeting_area_geometry", read_only=True)

    class Meta:
        model = CampaignArea
        fields = [
            "id",
            "campaign",
            "area_type",
            "city",
            "neighborhood",
            "center_point",
            "radius_meter",
            "suggested_route",
            "region_polygon",
            "targeting_geometry",
            "created_at",
            "updated_at",
        ]
