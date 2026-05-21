from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Trip
from campaigns.models import Campaign
from services.tasks import register_vehicle_task

@receiver(post_save, sender=Trip)
def register_vehicle_on_trip_creation(sender, instance, created, **kwargs):
    if not created:
        return  # فقط بار اول
    # اطمینان از اینکه کمپین فعال است
    if instance.campaign.status != Campaign.Status.ACTIVE:
        return

    vehicle = instance.vehicle
    driver = instance.driver
    driver_name = driver.full_name if hasattr(driver, 'full_name') else str(driver.user)
    created_at = instance.created_at
    updated_at = instance.updated_at

    register_vehicle_task.delay(
        vehicle_plate=vehicle.plate_number,
        display_name=f"{vehicle.plate_number} - {driver_name}",
        driver_id=driver.id,
        driver_name=driver_name,
        created_at=created_at,
        updated_at=updated_at,
    )