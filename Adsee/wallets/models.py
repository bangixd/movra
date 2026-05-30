from django.db import models
from django.conf import settings

class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet of {self.user.phone}"

class BankAccount(models.Model):
    driver = models.OneToOneField(
        'drivers.DriverProfile',
        on_delete=models.CASCADE,
        related_name='bank_account'
    )
    card_number = models.CharField(max_length=16, unique=True)
    sheba_number = models.CharField(max_length=26, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bank account of {self.driver.full_name}"

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

class ReferralReward(models.Model):
    driver = models.ForeignKey(
        'drivers.DriverProfile',
        on_delete=models.CASCADE,
        related_name='referral_rewards'
    )
    referred_driver = models.ForeignKey(
        'drivers.DriverProfile',
        on_delete=models.CASCADE,
        related_name='referred_rewards'
    )
    trip = models.ForeignKey(
        'trips.Trip',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reward for {self.driver.full_name} - {self.amount}"