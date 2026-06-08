from rest_framework import serializers
from campaigns.models import Campaign
from trips.models import Trip
from campaigns.serializers import DriverOnCampaignSerializer

class ClientCampaignSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='brand_name.name')
    region = serializers.SerializerMethodField()
    banner_type = serializers.CharField(source='design.banner_type.name', allow_null=True)
    print_shop_name = serializers.CharField(source='design.print_shop.shop_name', allow_null=True)
    print_shop_address = serializers.CharField(source='design.print_shop.address', allow_null=True)
    active_drivers = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            'id', 'slogan', 'brand_name', 'region', 'status',
            'start_date', 'end_date', 'banner_type',
            'print_shop_name', 'print_shop_address',
            'active_drivers'
        ]

    def get_region(self, obj):
        area = obj.area if hasattr(obj, 'area') else None
        if area:
            if area.area_type == 'CIRCLE' and area.neighborhood:
                return f"{area.city.name} - {area.neighborhood.name}"
            elif area.area_type == 'SUGGESTED_ROUTE' and area.suggested_route:
                return f"{area.city.name} - مسیر پیشنهادی"
            elif area.area_type == 'FREE_AREA':
                return area.city.name if area.city else "کل شهر"
        return None

    def get_active_drivers(self, obj):
        # فقط سفرهای فعال
        trips = Trip.objects.filter(
            campaign=obj,
            status__in=[Trip.Status.ACTIVE, Trip.Status.PAUSED]
        ).select_related('driver', 'vehicle', 'campaign__area__city')
        return DriverOnCampaignSerializer(trips, many=True).data