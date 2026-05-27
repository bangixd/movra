from rest_framework import serializers
from .models import SupportContent

class SupportContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportContent
        fields = ['id', 'type', 'title', 'body']