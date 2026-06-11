from django.db import models


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