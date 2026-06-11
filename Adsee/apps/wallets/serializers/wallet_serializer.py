from rest_framework import serializers
from wallets.models import Wallet, Transaction, BankAccount


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance']


class WalletSummarySerializer(serializers.ModelSerializer):
    card_number = serializers.CharField(source='driver.bank_account.card_number', read_only=True, default=None)
    sheba_number = serializers.CharField(source='driver.bank_account.sheba_number', read_only=True, default=None)
    bank_name = serializers.CharField(source='driver.bank_account.bank_name', read_only=True, default=None)

    class Meta:
        model = Wallet
        fields = ['total_earnings', 'balance', 'card_number', 'sheba_number', 'bank_name']