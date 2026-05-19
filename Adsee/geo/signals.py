from django.db.models.signals import post_save
from django.dispatch import receiver
from geo.models import DriverLocation
import logging
from services.tasks import forward_location_to_analytics_task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=DriverLocation)
def forward_location_to_analytics(sender, instance, created, **kwargs):
    if not created or not instance.trip_id:
        return

    trip = instance.trip
    vehicle = trip.vehicle
    campaign = trip.campaign

    forward_location_to_analytics_task.delay(
        driver_id=instance.driver_id,
        trip_id=trip.id,
        vehicle_plate=vehicle.plate_number,
        campaign_id=campaign.id,
        lat=instance.point.y,
        lon=instance.point.x,
        speed=0,
        heading=0,
        timestamp=int(instance.timestamp.timestamp())
    )