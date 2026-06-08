from rest_framework import serializers
from campaigns.models import CampaignGoal

class CampaignGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignGoal
        fields = '__all__'
