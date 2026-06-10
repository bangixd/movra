from rest_framework import serializers
from support.models import SiteSetting

class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = [
            'brand_name', 'brand_logo', 'about_text', 'about_image',
            'phone', 'email', 'address', 'social_links', 'referral_reward_amount'
        ]
