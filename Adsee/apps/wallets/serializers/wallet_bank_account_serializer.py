from rest_framework import serializers
from wallets.models import Wallet, Transaction, BankAccount


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ['card_number', 'sheba_number', 'bank_name', 'is_verified']
