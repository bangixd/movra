from clients.models import ClientDocument
from rest_framework import serializers

class ClientDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientDocument
        fields = ['id', 'user', 'document_type', 'file', 'status', 'submitted_at', 'reviewed_at', 'reject_reason']
        read_only_fields = ['user', 'status', 'submitted_at', 'reviewed_at', 'reject_reason']