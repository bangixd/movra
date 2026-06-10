from django.utils import timezone
from django.contrib.gis.geos import Point
from trips.models import Trip
from geo.models import DriverLocation
from services.tasks import forward_batch_locations_task

class DriverLocationService:
    """سرویس مدیریت موقعیت‌های راننده"""

    @staticmethod
    def get_queryset(user):
        """
        برگرداندن موقعیت‌ها بر اساس نقش کاربر.
        - ادمین: همهٔ موقعیت‌ها
        - راننده: فقط موقعیت‌های خودش
        """
        if not user.is_authenticated:
            return DriverLocation.objects.none()
        if user.is_staff:
            return DriverLocation.objects.all()
        return DriverLocation.objects.filter(driver=user)

    @staticmethod
    def get_active_trip(driver_profile):
        """
        یافتن سفر فعال راننده.
        Returns: Trip instance or None
        """
        return Trip.objects.filter(
            driver=driver_profile
        ).exclude(
            status__in=[Trip.Status.COMPLETED, Trip.Status.CANCELLED]
        ).first()

    @staticmethod
    def create_location(user, point_data) -> DriverLocation:
        """
        ایجاد یک موقعیت جدید برای راننده (real-time).
        Args:
            user: کاربر جاری
            point_data: dict حاوی 'point' (GeoJSON Point)
        Returns:
            DriverLocation ایجاد شده
        """
        point = point_data['point']
        lon = point['coordinates'][0]
        lat = point['coordinates'][1]

        # یافتن سفر فعال
        active_trip = DriverLocationService.get_active_trip(user.driver_profile)

        location = DriverLocation.objects.create(
            driver=user,
            trip=active_trip,
            point=Point(lon, lat, srid=4326),
            source='realtime'
        )
        return location

    @staticmethod
    def create_batch_locations(user, trip_id: int, points: list) -> list:
        """
        ایجاد دسته‌ای موقعیت‌ها (batch).
        Args:
            user: کاربر جاری
            trip_id: شناسهٔ سفر
            points: لیست نقاط
        Returns:
            لیست دیکشنری‌های موقعیت‌های ایجاد شده
        Raises:
            ValueError: اگر سفر یافت نشد یا فعال نباشد
        """
        try:
            trip = Trip.objects.get(id=trip_id, driver__user=user)
        except Trip.DoesNotExist:
            raise ValueError("سفر یافت نشد یا متعلق به شما نیست")

        if trip.status not in [Trip.Status.ACTIVE, Trip.Status.PAUSED]:
            raise ValueError("سفر فعال نیست")

        created_locations = []
        for point_data in points:
            lat = point_data['lat']
            lon = point_data['lon']
            ts = point_data.get('timestamp')

            if ts:
                from datetime import datetime, timezone as tz
                dt = datetime.fromtimestamp(ts, tz=tz.utc)
            else:
                dt = timezone.now()

            loc = DriverLocation.objects.create(
                driver=user,
                trip=trip,
                point=Point(lon, lat, srid=4326),
                timestamp=dt,
                source='batch'
            )
            created_locations.append({
                'id': loc.id,
                'point': {'lat': lat, 'lon': lon},
                'timestamp': loc.timestamp.isoformat()
            })

        # ارسال batch به سرویس Analytics (Celery)
        forward_batch_locations_task.delay(
            trip_id=trip.id,
            vehicle_plate=trip.vehicle.plate_number,
            campaign_id=trip.campaign.id,
            points=points
        )

        return created_locations