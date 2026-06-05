from rest_framework import serializers
from .models import Wallet, Transaction, BankAccount

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance']

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ['card_number', 'sheba_number', 'bank_name', 'is_verified']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'transaction_type', 'status', 'description', 'trip', 'created_at']
        read_only_fields = fields

class WalletSummarySerializer(serializers.ModelSerializer):
    card_number = serializers.CharField(source='driver.bank_account.card_number', read_only=True, default=None)
    sheba_number = serializers.CharField(source='driver.bank_account.sheba_number', read_only=True, default=None)
    bank_name = serializers.CharField(source='driver.bank_account.bank_name', read_only=True, default=None)

    class Meta:
        model = Wallet
        fields = ['total_earnings', 'balance', 'card_number', 'sheba_number', 'bank_name']