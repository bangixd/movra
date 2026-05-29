import time
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.gis.geos import Point

# ۱. کلاینت
from accounts.models import User
from clients.models import ClientProfile
client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
client_profile = ClientProfile.objects.create(user=client_user, full_name='Real Client', national_id='1234567890')

# ۲. برند
from brands.models import Brand
brand = Brand.objects.create(client=client_profile, name='Real Brand', slug='real-brand')

# ۳. نوع خودرو
from vehicles.models import VehicleType
vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)

# ۴. کمپین (ACTIVE)
from campaigns.models import Campaign, CampaignSetting
campaign = Campaign.objects.create(
    client=client_profile,
    slogan='Real Campaign',
    brand_name=brand,
    start_date=date.today(),
    status=Campaign.Status.ACTIVE
)
campaign_setting = CampaignSetting.objects.create(
    campaign=campaign,
    active_days=5,
    activity_hours_per_day='08:00:00',
    max_driver=2,
    vehicle_type=vehicle_type
)
print(f"Campaign created, end_date={campaign.end_date}")

# ۵. راننده و خودرو
from drivers.models import DriverProfile
driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
driver_profile = DriverProfile.objects.create(user=driver_user, first_name='Real', last_name='Driver', national_id='0987654321')

from vehicles.models import Vehicle
vehicle = Vehicle.objects.create(
    driver=driver_profile,
    vehicle_type=vehicle_type,
    plate_number='12A345B67',
    banner_max_width_cm=100,
    banner_max_height_cm=50
)
print(f"Vehicle created: {vehicle.plate_number}")

# ۶. ایجاد Trip (همینجا تسک register_vehicle_task به Celery ارسال می‌شود)
from trips.models import Trip
trip = Trip.objects.create(
    driver=driver_profile,
    campaign=campaign,
    vehicle=vehicle,
    status=Trip.Status.PENDING
)
from services.analytics_client import AnalyticsServiceClient
# Trip.objects.filter(driver=driver_profile).delete()
print(f"Trip created, id={trip.id}")

# صبر کن تا worker تسک ثبت خودرو را انجام دهد (چند ثانیه)
time.sleep(2)

# ۷. شروع سفر (بازهٔ زمانی ۱۰ دقیقه قبل)
trip.status = Trip.Status.ACTIVE
trip.start_time = timezone.now() - timedelta(minutes=10)
trip.save()
print(f"Trip started at {trip.start_time}")

# ۸. ارسال ۵ موقعیت مکانی با مختصات واقعی (هر بار تسک forward به Celery می‌رود)
for i, (lon, lat) in enumerate([
    (51.39, 35.70),
    (51.40, 35.71),
    (51.41, 35.72),
    (51.42, 35.73),
    (51.43, 35.74),
], 1):
    from geo.models import DriverLocation
    loc = DriverLocation.objects.create(
        driver=driver_user,
        trip=trip,
        point=Point(lon, lat, srid=4326)
    )
    print(f"Location {i} sent, id={loc.id}")
    time.sleep(0.5)  # کمی فاصله تا worker بتواند پردازش کند

# ۹. پایان سفر (تسک update_earnings_task به Celery می‌رود)
trip.status = Trip.Status.COMPLETED
trip.end_time = timezone.now()
trip.save()
print(f"Trip completed at {trip.end_time}")

# ۱۰. انتظار برای اجرای تسک واکشی درآمد توسط worker
time.sleep(3)

# ۱۱. بررسی نتیجه
trip.refresh_from_db()
print(f"Trip status: {trip.status}")
print(f"EARNINGS: {trip.earnings} Toman")