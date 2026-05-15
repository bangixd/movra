from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DriverLocation


@receiver(post_save, sender=DriverLocation)
def send_location_to_income_api(sender, instance, created, **kwargs):
    if created and instance.trip_id:  # فقط اگر مربوط به سفر باشد
        # اینجا API خارجی را صدا بزن
        # external_api.calculate_income(driver_id=..., location=..., ...)
        pass