from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Vehicle
import logging
from services.tasks import register_vehicle_task

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Vehicle)
def register_vehicle_in_analytics(sender, instance, created, **kwargs):
    if not created:
        return
    register_vehicle_task.delay(
        vehicle_plate=instance.plate_number,
        display_name=str(instance)
    )