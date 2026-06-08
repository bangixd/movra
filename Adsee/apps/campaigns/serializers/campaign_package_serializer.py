from rest_framework import serializers
from campaigns.models import CampaignPackage

class CampaignPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignPackage
        fields = '__all__'
