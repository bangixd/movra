from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DriverLocation
from services.analytics_client import AnalyticsServiceClient
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=DriverLocation)
def forward_location_to_analytics(sender, instance, created, **kwargs):
    if not created or not instance.trip_id:
        return  # فقط موقعیت‌های جدید و متصل به سفر

    try:
        client = AnalyticsServiceClient()
        # تبدیل Point به lat/lon
        lat = instance.point.y
        lon = instance.point.x

        # timestamp باید به Unix timestamp (ثانیه) تبدیل شود
        ts = int(instance.timestamp.timestamp())

        # خواندن شناسه‌ها
        vehicle = instance.trip.vehicle
        campaign = instance.trip.campaign

        client.send_single_location(
            vehicle_id=vehicle.plate_number,         # شناسه یکتا (پلاک)
            vehicle_display_name=str(vehicle),       # مثلاً "12A345B67 (Sedan)"
            campaign_id=str(campaign.id),            # شناسه کمپین
            session_id=str(instance.trip.id),        # شناسه سفر
            lat=lat,
            lon=lon,
            speed=0,          # اگر سرعت در DriverLocation نداری، صفر بذار
            heading=0,        # اگر جهت نداری، صفر
            timestamp=ts
        )
        logger.info(f"Location forwarded for trip {instance.trip_id}")
    except Exception as e:
        logger.error(f"Failed to forward location: {e}")