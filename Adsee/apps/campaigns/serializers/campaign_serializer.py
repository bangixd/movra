from rest_framework import serializers
from campaigns.models import Campaign
from rest_framework_gis import serializers as gis_serializers
from .client_profile_mini_serializer import ClientProfileMiniSerializer
from .brand_mini_serializer import BrandMiniSerializer

class CampaignSerializer(serializers.ModelSerializer):
    client_detail = ClientProfileMiniSerializer(source='client', read_only=True)
    brand_detail = BrandMiniSerializer(source='brand_name', read_only=True)
    region = gis_serializers.GeometryField(source='area.region_polygon', read_only=True)


    class Meta:
        model = Campaign
        fields = [
            'id',
            'client',
            'client_detail',
            'slogan',
            'goal',
            'brand_name',
            'brand_detail',
            'region',
            'description',
            'start_date',
            'end_date',
            'status',
            'is_deleted',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['client', 'is_deleted', 'created_at', 'updated_at', 'start_date', 'end_date']

    def validate(self, attrs):
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': 'end_date must be greater than or equal to start_date.'
            })

        return attrs
