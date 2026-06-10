from rest_framework import serializers
from support.models import AppDownloadLink

class AppDownloadLinkSerializer(serializers.ModelSerializer):
    platform_label = serializers.CharField(source='get_platform_display', read_only=True)

    class Meta:
        model = AppDownloadLink
        fields = ['id', 'platform', 'platform_label', 'version', 'url', 'description', 'is_active']