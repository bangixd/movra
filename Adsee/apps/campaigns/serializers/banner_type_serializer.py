from rest_framework import serializers
from campaigns.models import BannerType

from geo.models import DriverLocation

class BannerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerType
        fields = '__all__'
