from rest_framework import serializers
from support.models import FAQItem

class FAQItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = ['id', 'question', 'answer']

class FAQItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = ['id', 'category', 'question', 'answer', 'order', 'is_active']

class FAQItemReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQItem
        fields = ['id', 'category', 'question', 'answer', 'order', 'is_active']
