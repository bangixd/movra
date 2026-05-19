from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Vehicle
from services.analytics_client import AnalyticsServiceClient
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Vehicle)
def register_vehicle_in_analytics(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        client = AnalyticsServiceClient()
        display_name = str(instance)   # مثلاً "12A345B67 (Sedan)"
        client.register_vehicle(
            vehicle_id=instance.plate_number,
            vehicle_display_name=display_name
        )
        logger.info(f"Vehicle {instance.plate_number} registered in analytics")
    except Exception as e:
        logger.error(f"Failed to register vehicle {instance.plate_number}: {e}")