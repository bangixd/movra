from rest_framework import serializers
from campaigns.models import CampaignArea
from geo.models import SuggestedRoute


class CampaignAreaCreateSerializer(serializers.ModelSerializer):
    suggested_routes = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=SuggestedRoute.objects.all(),
        required=False
    )

    class Meta:
        model = CampaignArea
        fields = [
            "id",
            "campaign",
            "area_type",
            "city",
            "neighborhood",
            "center_point",
            "suggested_routes",
            "region_polygon",
        ]

    def validate_campaign(self, campaign):
        request = self.context.get("request")
        if request and campaign.owner_id != request.user.id:
            raise serializers.ValidationError("You do not have access to this campaign.")
        return campaign

    def validate(self, attrs):
        instance = getattr(self, "instance", None)

        area_type = attrs.get("area_type", getattr(instance, "area_type", None))
        city = attrs.get("city", getattr(instance, "city", None))
        neighborhood = attrs.get("neighborhood", getattr(instance, "neighborhood", None))
        center_point = attrs.get("center_point", getattr(instance, "center_point", None))
        suggested_routes = attrs.get("suggested_routes", getattr(instance, "suggested_routes", None))
        region_polygon = attrs.get("region_polygon", getattr(instance, "region_polygon", None))
        campaign = attrs.get("campaign", getattr(instance, "campaign", None))

        if not area_type:
            raise serializers.ValidationError({"area_type": "This field is required."})

        # OneToOne validation for create
        if not instance and campaign and CampaignArea.objects.filter(campaign=campaign).exists():
            raise serializers.ValidationError({
                "campaign": "A CampaignArea already exists for this campaign."
            })

        # Optional consistency checks
        if neighborhood and city and neighborhood.city_id != city.id:
            raise serializers.ValidationError({
                "neighborhood": "This neighborhood does not belong to the selected city."
            })

        if area_type == CampaignArea.AreaType.CIRCLE:
            errors = {}

            if not city:
                errors["city"] = "This field is required for CIRCLE."
            if not neighborhood:
                errors["neighborhood"] = "This field is required for CIRCLE."
            if not center_point:
                errors["center_point"] = "This field is required for CIRCLE."

            if suggested_routes:
                errors["suggested_route"] = "This field must not be set for CIRCLE."
            if region_polygon:
                errors["region_polygon"] = "This field must not be set for CIRCLE."

            if errors:
                raise serializers.ValidationError(errors)

        elif area_type == CampaignArea.AreaType.SUGGESTED_ROUTE:
            errors = {}
            if not city:
                errors["city"] = "This field is required for SUGGESTED_ROUTE."
            if not neighborhood:
                errors["neighborhood"] = "This field is required for SUGGESTED_ROUTE."
            if not suggested_routes:
                errors["suggested_routes"] = "At least one suggested route is required."

            if center_point:
                errors["center_point"] = "This field must not be set for SUGGESTED_ROUTE."
            if region_polygon:
                errors["region_polygon"] = "This field must not be set for SUGGESTED_ROUTE."

            if errors:
                raise serializers.ValidationError(errors)

        elif area_type == CampaignArea.AreaType.FREE_AREA:
            errors = {}

            if not region_polygon:
                errors["region_polygon"] = "This field is required for FREE_AREA."

            if city:
                errors["city"] = "This field must not be set for FREE_AREA."
            if neighborhood:
                errors["neighborhood"] = "This field must not be set for FREE_AREA."
            if center_point:
                errors["center_point"] = "This field must not be set for FREE_AREA."
            if suggested_routes:
                errors["suggested_route"] = "This field must not be set for FREE_AREA."

            if errors:
                raise serializers.ValidationError(errors)

        else:
            raise serializers.ValidationError({
                "area_type": "Invalid area_type."
            })

        return attrs

