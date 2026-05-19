from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DriverLocation
from services.analytics_client import AnalyticsServiceClient
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=DriverLocation)
def forward_location_to_analytics(sender, instance, created, **kwargs):
    if not created or not instance.trip_id:
        return

    try:
        trip = instance.trip
        vehicle = trip.vehicle
        campaign = trip.campaign

        client = AnalyticsServiceClient()
        lat = instance.point.y
        lon = instance.point.x
        ts = int(instance.timestamp.timestamp())

        client.send_single_location(
            vehicle_id=vehicle.plate_number,
            vehicle_display_name=str(vehicle),
            campaign_id=str(campaign.id),
            session_id=str(trip.id),
            lat=lat,
            lon=lon,
            speed=0,      # اگر در DriverLocation سرعت ندارید، ۰ بفرستید
            heading=0,
            timestamp=ts
        )
        logger.info(f"Location forwarded for trip {trip.id}")
    except Exception as e:
        logger.error(f"Failed to forward location: {e}")