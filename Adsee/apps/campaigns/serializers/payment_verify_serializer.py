from rest_framework import serializers

class PaymentVerifySerializer(serializers.Serializer):
    authority = serializers.CharField(max_length=200, required=True)
    status = serializers.CharField(max_length=10, required=True)  # OK / NOK
