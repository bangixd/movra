from celery import shared_task
from services.analytics_client import AnalyticsServiceClient
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def forward_location_to_analytics_task(self, driver_id, trip_id,
                                       vehicle_plate, campaign_id,
                                       lat, lon, speed, heading, timestamp):
    """ارسال یک موقعیت به سرویس Analytics (آسنکرون)"""
    client = AnalyticsServiceClient()
    try:
        client.send_single_location(
            vehicle_id=vehicle_plate,
            campaign_id=str(campaign_id),
            session_id=str(trip_id),
            lat=lat, lon=lon,
            speed=speed, heading=heading,
            timestamp=timestamp
        )
    except Exception as exc:
        logger.error(f"Location forwarding failed (retry {self.request.retries}): {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def register_vehicle_task(self, vehicle_plate, display_name,
                          driver_id=None, driver_name=None, driver_phone=None,
                          campaign_id=None):   # ← پارامتر جدید
    client = AnalyticsServiceClient()
    payload = {
        "vehicle_id": vehicle_plate,
        "vehicle_display_name": display_name
    }
    if driver_id:
        payload["driver_id"] = driver_id
    if driver_name:
        payload["driver_name"] = driver_name
    if driver_phone:
        payload["driver_phone"] = driver_phone
    if campaign_id:
        payload["campaign_id"] = campaign_id

    try:
        client.register_vehicle(vehicle_plate, display_name, extra_fields=payload)
    except Exception as exc:
        logger.error(f"Vehicle registration failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def update_earnings_task(self, trip_id):
    """واکشی درآمد از سرویس Analytics و ذخیره در Trip"""
    from trips.models import Trip
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return

    if not (trip.start_time and trip.end_time):
        return

    client = AnalyticsServiceClient()
    start_ts = int(trip.start_time.timestamp())
    end_ts = int(trip.end_time.timestamp())

    try:
        result = client.calculate_earnings(
            vehicle_id=trip.vehicle.plate_number,
            start_ts=start_ts,
            end_ts=end_ts
        )
        trip.earnings = result.get("earnings", 0)
        trip.save(update_fields=["earnings"])
    except Exception as exc:
        logger.error(f"Earnings update failed for trip {trip_id}: {exc}")
        # در صورت شکست نهایی، می‌توان دوباره تلاش کرد یا earnings صفر ماند