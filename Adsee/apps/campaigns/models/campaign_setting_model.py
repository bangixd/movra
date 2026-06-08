from django.db import models

class CampaignSetting(models.Model):
    campaign = models.OneToOneField('Campaign', on_delete=models.CASCADE, related_name='setting')

    active_days = models.PositiveIntegerField()
    activity_hours_per_day = models.TimeField()

    max_driver = models.PositiveIntegerField()

    vehicle_type = models.ForeignKey(
        "vehicles.VehicleType",
        on_delete=models.PROTECT,
        related_name="campaigns"
    )

