from django.utils import timezone
from datetime import date
from accounts.models import User, ClientProfile, DriverProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting
from geo.models import City, DriverLocation
from trips.models import Trip
from django.contrib.gis.geos import Point

# ---------- 1. ساخت کاربر و پروفایل کلاینت ----------
client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
client_profile = ClientProfile.objects.create(
    user=client_user,
    full_name='Client Test',
    national_id='1234567890'
)
print("Client created:", client_user)

# ---------- 2. ساخت برند ----------
brand = Brand.objects.create(
    client=client_profile,
    name='Test Brand',
    slug='test-brand'
)
print("Brand created:", brand)

# ---------- 3. ساخت نوع خودرو ----------
vehicle_type = VehicleType.objects.create(
    name='Sedan',
    base_hourly_rate=50000
)
print("VehicleType created:", vehicle_type)

# ---------- 4. ساخت کمپین با تاریخ شروع امروز ----------
campaign = Campaign.objects.create(
    client=client_profile,
    slogan='Test Campaign',
    brand_name=brand,
    start_date=date.today(),
    status=Campaign.Status.ACTIVE
)
print("Campaign created:", campaign)

# ---------- 5. ساخت تنظیمات کمپین (با active_days=5 → end_date خودکار) ----------
campaign_setting = CampaignSetting.objects.create(
    campaign=campaign,
    active_days=5,
    activity_hours_per_day='08:00:00',
    max_driver=2,
    vehicle_type=vehicle_type
)
print("CampaignSetting created. Campaign end_date:", campaign.end_date)

# ---------- 6. ساخت کاربر و پروفایل راننده ----------
driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
driver_profile = DriverProfile.objects.create(
    user=driver_user,
    full_name='Driver Test',
    national_id='0987654321'
)
print("Driver created:", driver_user)

# ---------- 7. ساخت خودرو برای راننده (با پلاک یکتا) ----------
# هنگام ذخیره، سیگنال آن را در سرویس Analytics ثبت می‌کند
vehicle = Vehicle.objects.create(
    driver=driver_profile,
    vehicle_type=vehicle_type,
    plate_number='12A345B67',
    banner_max_width_cm=150,
    banner_max_height_cm=80
)
print("Vehicle created. Check analytics registration log in Django console.")

# ---------- 8. ایجاد Trip ----------
trip = Trip.objects.create(
    driver=driver_profile,
    campaign=campaign,
    vehicle=vehicle,
    status=Trip.Status.PENDING
)
print("Trip created:", trip)

# ---------- 9. شروع سفر ----------
trip.status = Trip.Status.ACTIVE
trip.start_time = timezone.now()
trip.save()
print("Trip started at", trip.start_time)

# ---------- 10. ارسال موقعیت اول ----------
loc1 = DriverLocation.objects.create(
    driver=driver_user,       # توجه: DriverLocation.driver به User اشاره دارد
    trip=trip,
    point=Point(51.39, 35.70, srid=4326),  # lon, lat
)
print("Location 1 sent. Check analytics log.")

# ---------- 11. ارسال موقعیت دوم (بعد از چند ثانیه فرضی) ----------
import time
time.sleep(1)  # فقط برای شبیه‌سازی تأخیر زمانی
loc2 = DriverLocation.objects.create(
    driver=driver_user,
    trip=trip,
    point=Point(51.40, 35.71, srid=4326),
)
print("Location 2 sent.")

# ---------- 12. ارسال موقعیت سوم ----------
loc3 = DriverLocation.objects.create(
    driver=driver_user,
    trip=trip,
    point=Point(51.41, 35.72, srid=4326),
)
print("Location 3 sent.")

# ---------- 13. پایان سفر ----------
trip.status = Trip.Status.COMPLETED
trip.end_time = timezone.now()
trip.save()

# کد complete در ViewSet (که اینجا باید دستی صدا کنیم یا مستقیماً earnings را بگیریم)
# از آنجایی که ما در shell هستیم و ViewSet در دسترس نیست،
# مستقیماً تابع کلاینت را برای محاسبه درآمد صدا می‌زنیم:

from services.analytics_client import AnalyticsServiceClient
client = AnalyticsServiceClient()
start_ts = int(trip.start_time.timestamp())
end_ts = int(trip.end_time.timestamp())

try:
    result = client.calculate_earnings(
        vehicle_id=vehicle.plate_number,
        start_ts=start_ts,
        end_ts=end_ts
    )
    trip.earnings = result.get("earnings", 0)
    trip.save(update_fields=["earnings"])
    print(f"Earnings calculated: {trip.earnings} Toman")
except Exception as e:
    print(f"Error fetching earnings: {e}")