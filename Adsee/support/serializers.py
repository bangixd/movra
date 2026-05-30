from rest_framework import serializers
from .models import SupportContent, SiteSetting, Ticket, FAQCategory, FAQItem, AppDownloadLink


class SupportContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportContent
        fields = ['id', 'type', 'title', 'body']


class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = [
            'brand_name', 'brand_logo', 'about_text', 'about_image',
            'phone', 'email', 'address', 'social_links', 'referral_reward_amount'
        ]

class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['subject', 'name', 'phone', 'message']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class TicketListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'subject', 'status', 'created_at']
        read_only_fields = fields

class FAQItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = ['id', 'question', 'answer']

class FAQCategorySerializer(serializers.ModelSerializer):
    faqs = FAQItemSerializer(many=True, read_only=True)

    class Meta:
        model = FAQCategory
        fields = ['id', 'name', 'icon', 'faqs']


# ---------- FAQ Category & Item ----------
class FAQItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = ['id', 'category', 'question', 'answer', 'order', 'is_active']

class FAQItemReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = ['id', 'category', 'question', 'answer', 'order', 'is_active']

class FAQCategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQCategory
        fields = ['id', 'name', 'icon', 'order', 'is_active']

class FAQCategoryReadSerializer(serializers.ModelSerializer):
    faqs = FAQItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = FAQCategory
        fields = ['id', 'name', 'icon', 'order', 'is_active', 'faqs']


# ---------- Ticket ----------
class TicketAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'user', 'subject', 'name', 'phone', 'message', 'status', 'created_at']
        read_only_fields = ['user', 'subject', 'name', 'phone', 'message', 'created_at']

#----------- DOWNLOAD LINK -----------#
class AppDownloadLinkSerializer(serializers.ModelSerializer):
    platform_label = serializers.CharField(source='get_platform_display', read_only=True)

    class Meta:
        model = AppDownloadLink
        fields = ['id', 'platform', 'platform_label', 'version', 'url', 'description', 'is_active']