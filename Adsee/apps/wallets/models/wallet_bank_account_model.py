from django.db import models


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
