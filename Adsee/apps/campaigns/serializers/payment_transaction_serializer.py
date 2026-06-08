from rest_framework import serializers
from campaigns.models import PaymentTransaction

class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ['id', 'invoice', 'authority', 'ref_id', 'amount', 'status', 'created_at']
        read_only_fields = fields
