from rest_framework import serializers
from support.models import FAQCategory
from .support_FAQ_item_serializer import FAQItemSerializer, FAQItemReadSerializer

class FAQCategorySerializer(serializers.ModelSerializer):
    faqs = FAQItemSerializer(many=True, read_only=True)

    class Meta:
        model = FAQCategory
        fields = ['id', 'name', 'icon', 'faqs']

class FAQCategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQCategory
        fields = ['id', 'name', 'icon', 'order', 'is_active']

class FAQCategoryReadSerializer(serializers.ModelSerializer):
    faqs = FAQItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = FAQCategory
        fields = ['id', 'name', 'icon', 'order', 'is_active', 'faqs']
