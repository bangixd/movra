from rest_framework import serializers
from support.models import Ticket

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

class TicketAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'user', 'subject', 'name', 'phone', 'message', 'status', 'created_at']
        read_only_fields = ['user', 'subject', 'name', 'phone', 'message', 'created_at']
