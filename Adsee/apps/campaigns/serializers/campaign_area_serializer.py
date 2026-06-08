from rest_framework import serializers
from campaigns.models import CampaignArea

from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeometryField

class CampaignAreaSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = CampaignArea
        fields = [
            "id",
            "campaign",
            "area_type",

            # City + Neighborhood
            "city",
            "neighborhood",

            # Circle
            "center_point",
            "radius_meter",

            # Suggested Route
            "suggested_route",

            # Free Polygon
            "region_polygon",

            "created_at",
            "updated_at",
        ]

        geo_field = "region_polygon"  # فقط برای FREE_AREA استفاده می‌شود

    # ----------------- VALIDATION -----------------

    def validate(self, attrs):
        area_type = attrs.get("area_type") or self.instance.area_type if self.instance else None

        city = attrs.get("city")
        neighborhood = attrs.get("neighborhood")

        center_point = attrs.get("center_point")
        radius_meter = attrs.get("radius_meter")

        suggested_route = attrs.get("suggested_route")
        region_polygon = attrs.get("region_polygon")

        # ------------------- CIRCLE -------------------
        if area_type == CampaignArea.AreaType.CIRCLE:
            missing = []
            if not city:
                missing.append("city")
            if not neighborhood:
                missing.append("neighborhood")
            if not center_point:
                missing.append("center_point")
            if not radius_meter:
                missing.append("radius_meter")

            if missing:
                raise serializers.ValidationError({
                    "detail": f"For CIRCLE mode, these fields are required: {', '.join(missing)}"
                })

            # فیلدهای نباید پر شوند
            forbidden = {
                "suggested_route": suggested_route,
                "region_polygon": region_polygon,
            }
            for name, value in forbidden.items():
                if value:
                    raise serializers.ValidationError({
                        name: f"{name} must NOT be provided when area_type is CIRCLE."
                    })

        # ------------------- SUGGESTED ROUTE -------------------
        elif area_type == CampaignArea.AreaType.SUGGESTED_ROUTE:
            if not city or not neighborhood:
                raise serializers.ValidationError({
                    "detail": "city and neighborhood are required for SUGGESTED_ROUTE."
                })

            if not suggested_route:
                raise serializers.ValidationError({
                    "suggested_route": "This field is required for SUGGESTED_ROUTE."
                })

            forbidden = {
                "center_point": center_point,
                "radius_meter": radius_meter,
                "region_polygon": region_polygon,
            }
            for name, value in forbidden.items():
                if value:
                    raise serializers.ValidationError({
                        name: f"{name} must NOT be provided when area_type is SUGGESTED_ROUTE."
                    })

        # ------------------- FREE POLYGON -------------------
        elif area_type == CampaignArea.AreaType.FREE_AREA:
            if not region_polygon:
                raise serializers.ValidationError({
                    "region_polygon": "region_polygon is required for FREE_AREA."
                })

            forbidden = {
                "city": city,
                "neighborhood": neighborhood,
                "center_point": center_point,
                "radius_meter": radius_meter,
                "suggested_route": suggested_route,
            }
            for name, value in forbidden.items():
                if value:
                    raise serializers.ValidationError({
                        name: f"{name} must NOT be provided when area_type is FREE_AREA."
                    })

        else:
            raise serializers.ValidationError({
                "area_type": "Invalid area_type."
            })

        return attrs