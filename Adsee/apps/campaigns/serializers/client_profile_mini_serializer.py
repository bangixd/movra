from rest_framework import serializers
from clients.models import ClientProfile

class ClientProfileMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ['id', 'full_name']
