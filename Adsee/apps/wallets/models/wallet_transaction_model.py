from django.db import models
from .wallet_model import  Wallet

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'درآمد'
        WITHDRAWAL = 'WITHDRAWAL', 'برداشت'
        DEPOSIT = 'DEPOSIT', 'شارژ کیف پول'
        BONUS = 'BONUS', 'پاداش'
        REFUND = 'REFUND', 'بازگشت'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار'
        SUCCESS = 'SUCCESS', 'موفق'
        FAILED = 'FAILED', 'ناموفق'

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    description = models.CharField(max_length=255, blank=True)
    trip = models.ForeignKey(
        'trips.Trip',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='wallet_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} - {self.status}"
