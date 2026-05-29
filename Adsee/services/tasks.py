from celery import shared_task
from services.analytics_client import AnalyticsServiceClient
from services.sms_client import MeliPayamakClient
from clients.models import ClientDocument
from trips.models import Trip, TripAnalysis
from campaigns.models import CampaignInvoice
from django.utils import timezone
import time

import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_driver_document(self, document_id):
    from drivers.models import DriverDocument
    import time

    try:
        doc = DriverDocument.objects.get(id=document_id)
    except DriverDocument.DoesNotExist:
        return

    # شبیه‌سازی یک پردازش سنگین (مثلاً بررسی سایز، ارسال به KYC)
    time.sleep(2)  # بعداً حذف شود
    # مثلاً می‌توانید سایز فایل را چک کنید
    # file_size = doc.file.size
    # if file_size > 10 * 1024 * 1024:  # بزرگتر از ۱۰ مگابایت
    #     doc.status = DriverDocument.ApprovalStatus.REJECTED
    #     doc.reject_reason = "حجم فایل بیش از حد مجاز است"
    #     doc.save()
    #     return

    doc.processed = True
    doc.save()
    logger.info(f"Document {document_id} processed successfully")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_client_document(self, document_id):

    try:
        doc = ClientDocument.objects.get(id=document_id)
    except ClientDocument.DoesNotExist:
        return

    # همان پردازش شبیه‌سازی‌شده
    time.sleep(2)
    doc.processed = True
    doc.save()
    logger.info(f"Client document {document_id} processed successfully")


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
                          created_at=None, updated_at=None):   # ← پارامتر جدید
    client = AnalyticsServiceClient()
    payload = {
        "vehicle_id": vehicle_plate,
        "display_name": display_name
    }
    if driver_id:
        payload["driver_id"] = driver_id
    if driver_name:
        payload["driver_name"] = driver_name
    if driver_phone:
        payload["driver_phone"] = driver_phone
    if created_at:
        payload["created_at"] = created_at
    if updated_at:
        payload["updated_at"] = updated_at

    try:
        client.register_vehicle(vehicle_plate, display_name, extra_fields=payload)
    except Exception as exc:
        logger.error(f"Vehicle registration failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def update_earnings_task(self, trip_id):
    """واکشی درآمد از سرویس Analytics و ذخیره در Trip"""
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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def forward_batch_locations_task(self, trip_id, vehicle_plate, campaign_id, points):
    """ارسال دسته‌ای نقاط به سرویس Analytics"""
    client = AnalyticsServiceClient()
    batch_payload = []
    for p in points:
        batch_payload.append({
            "vehicle_id": vehicle_plate,
            "campaign_id": str(campaign_id),
            "session_id": str(trip_id),
            "lat": p['lat'],
            "lon": p['lon'],
            "speed": p.get('speed', 0),
            "heading": p.get('heading', 0),
            "timestamp": p['timestamp']
        })

    try:
        client.send_batch_locations(batch_payload)  # این متد را باید به کلاینت اضافه کنیم
    except Exception as exc:
        logger.error(f"Batch forwarding failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def fetch_and_store_trip_analysis(self, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return

    if not (trip.start_time and trip.end_time):
        return

    vehicle_id = trip.vehicle.plate_number
    start_ts = int(trip.start_time.timestamp())
    end_ts = int(trip.end_time.timestamp())

    client = AnalyticsServiceClient()
    try:
        # گرفتن خلاصه
        summary = client.get_analysis_summary(vehicle_id, start_ts, end_ts)
        # ایجاد analysis-run و گرفتن run_id
        run_result = client.create_analysis_run(vehicle_id, start_ts, end_ts)
        run_id = run_result.get('run_id')
    except Exception as exc:
        raise self.retry(exc=exc)

    # ذخیره در TripAnalysis
    TripAnalysis.objects.update_or_create(
        trip=trip,
        defaults={
            'active_seconds': summary.get('active_seconds', 0),
            'distance_km': summary.get('distance_km', 0),
            'exposure_score': summary.get('exposure_score', 0),
            'estimated_impressions': summary.get('estimated_impressions', 0),
            'data_quality': summary.get('data_quality', 0),
            'confidence': summary.get('confidence', 0),
            'avg_traffic_ratio': summary.get('avg_traffic_ratio', 0),
            'raw_response': summary,
            'analysis_run_id': run_id,
        }
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_otp_sms_task(self, phone, code):
    client = MeliPayamakClient()
    message = f'کد تأیید شما: {code}\nلغو11'
    success, status = client.send_sms(phone, message)
    if not success:
        raise self.retry(exc=Exception(f"SMS failed: {status}"))


# services/tasks.py
@shared_task
def expire_pending_invoices():
    now = timezone.now()
    invoices = CampaignInvoice.objects.filter(
        status=CampaignInvoice.Status.ISSUED,
        expires_at__lte=now
    )
    count = invoices.update(status=CampaignInvoice.Status.EXPIRED)
    if count:
        logger.info(f"Expired {count} invoices")

