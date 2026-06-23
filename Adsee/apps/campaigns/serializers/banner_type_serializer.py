from rest_framework import serializers
from campaigns.models import BannerType


class BannerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerType
        fields = '__all__'
