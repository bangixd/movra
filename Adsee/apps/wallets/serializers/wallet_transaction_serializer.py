from rest_framework import serializers
from wallets.models import Wallet, Transaction, BankAccount


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'transaction_type', 'status', 'description', 'trip', 'created_at']
        read_only_fields = fields
