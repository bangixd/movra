from rest_framework import serializers

class PaymentRequestSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField(required=True)
