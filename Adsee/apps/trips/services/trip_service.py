import logging
from django.utils import timezone
from campaigns.models import Campaign
from trips.models import Trip, TripAnalysis
from trips.serializers import InstallationUploadSerializer
from services.analytics_client import AnalyticsServiceClient
from services.tasks import fetch_and_store_trip_analysis

logger = logging.getLogger(__name__)


class TripService:
    """سرویس مدیریت سفرها"""

    @staticmethod
    def get_queryset(user):
        """برگرداندن سفرهای کاربر جاری (ادمین: همه، راننده: خودش)"""
        if not user.is_authenticated:
            return Trip.objects.none()
        if user.is_staff:
            return Trip.objects.all()
        return Trip.objects.filter(driver__user=user)

    @staticmethod
    def get_active_trip(user):
        """سفر فعال راننده (PENDING/ACTIVE/PAUSED) یا None"""
        return Trip.objects.filter(
            driver__user=user
        ).exclude(
            status__in=[Trip.Status.COMPLETED, Trip.Status.CANCELLED]
        ).first()

    @staticmethod
    def get_available_campaigns(city_id=None):
        """کمپین‌های فعال برای نمایش به راننده"""
        now = timezone.datetime.now()
        campaigns = Campaign.objects.filter(
            status=Campaign.Status.ACTIVE,
            start_date__lte=now.date(),
            end_date__gte=now.date()
        )
        if city_id:
            campaigns = campaigns.filter(area__city__id=city_id)
        return campaigns

    # ---------- عملیات تغییر وضعیت ----------
    @staticmethod
    def start_trip(trip, user):
        if trip.driver.user_id != user.id:
            raise PermissionError("شما مالک این سفر نیستید")
        if trip.status != Trip.Status.PENDING:
            raise ValueError("فقط سفرهای در انتظار می‌توانند شروع شوند")
        trip.status = Trip.Status.ACTIVE
        trip.start_time = timezone.now()
        trip.save()
        return trip

    @staticmethod
    def pause_trip(trip, user):
        if trip.driver.user_id != user.id:
            raise PermissionError("شما مالک این سفر نیستید")
        if trip.status != Trip.Status.ACTIVE:
            raise ValueError("فقط سفرهای فعال می‌توانند توقف کنند")
        trip.status = Trip.Status.PAUSED
        trip.save()
        return trip

    @staticmethod
    def resume_trip(trip, user):
        if trip.driver.user_id != user.id:
            raise PermissionError("شما مالک این سفر نیستید")
        if trip.status != Trip.Status.PAUSED:
            raise ValueError("فقط سفرهای توقف‌شده می‌توانند ادامه یابند")
        trip.status = Trip.Status.ACTIVE
        trip.save()
        return trip

    @staticmethod
    def cancel_trip(trip, user):
        if trip.driver.user_id != user.id:
            raise PermissionError("شما مالک این سفر نیستید")
        if trip.status in [Trip.Status.COMPLETED, Trip.Status.CANCELLED]:
            raise ValueError("این سفر قبلاً پایان یافته است")
        trip.status = Trip.Status.CANCELLED
        trip.end_time = timezone.now()
        trip.save()
        return trip

    @staticmethod
    def complete_trip(trip, user):
        if trip.driver.user_id != user.id:
            raise PermissionError("شما مالک این سفر نیستید")
        if trip.status not in [Trip.Status.ACTIVE, Trip.Status.PAUSED]:
            raise ValueError("فقط سفرهای فعال/توقف‌شده می‌توانند پایان یابند")

        trip.status = Trip.Status.COMPLETED
        trip.end_time = timezone.now()
        trip.save()

        # محاسبهٔ درآمد (تلاش مستقیم، در صورت خطا earnings صفر می‌ماند)
        try:
            client = AnalyticsServiceClient()
            start_ts = int(trip.start_time.timestamp())
            end_ts = int(trip.end_time.timestamp())
            result = client.calculate_earnings(
                vehicle_id=trip.vehicle.plate_number,
                start_ts=start_ts,
                end_ts=end_ts
            )
            trip.earnings = result.get("earnings", 0)
            trip.save(update_fields=["earnings"])
            # درخواست تحلیل در پس‌زمینه
            fetch_and_store_trip_analysis.delay(trip.id)
        except Exception as e:
            logger.error(f"Earnings calculation failed for trip {trip.id}: {e}")

        return trip

    # ---------- تحلیل ----------
    @staticmethod
    def get_trip_analysis(trip, user):
        if trip.driver.user_id != user.id and not user.is_staff:
            raise PermissionError("دسترسی غیرمجاز")
        try:
            return trip.analysis
        except TripAnalysis.DoesNotExist:
            return None

    @staticmethod
    def refresh_analysis(trip, user):
        if trip.driver.user_id != user.id and not user.is_staff:
            raise PermissionError("دسترسی غیرمجاز")
        fetch_and_store_trip_analysis.delay(trip.id)

    # ---------- درآمد جاری ----------
    @staticmethod
    def get_current_earnings(trip, user):
        if trip.driver.user != user and not user.is_staff:
            raise PermissionError("دسترسی غیرمجاز")
        if not trip.start_time:
            return {"earnings": 0}

        end_ts = int(timezone.now().timestamp())
        start_ts = int(trip.start_time.timestamp())
        client = AnalyticsServiceClient()
        result = client.calculate_earnings(trip.vehicle.plate_number, start_ts, end_ts)
        return result

    # ---------- آپلود عکس نصب ----------
    @staticmethod
    def upload_installation(trip, user, data):
        if trip.driver.user != user:
            raise PermissionError("دسترسی غیرمجاز")

        from trips.serializers import InstallationUploadSerializer
        serializer = InstallationUploadSerializer(trip, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if trip.sticker_image and trip.driver_car_image:
            trip.installation_verified = True
            trip.installation_verified_at = timezone.now()
            trip.save()
        return trip