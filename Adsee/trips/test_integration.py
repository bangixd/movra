from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.gis.geos import Point, Polygon

from accounts.models import User
from drivers.models import DriverProfile
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import (
    Campaign, CampaignSetting, CampaignArea, CampaignInvoice
)
from geo.models import Province, City
from trips.models import Trip


class FullFlowIntegrationTest(TestCase):
    def setUp(self):
        # ================ 1. آماده‌سازی داده‌های پایه ================
        # استان و شهر (با مختصات معتبر برای GIS)
        self.province = Province.objects.create(name='Tehran')
        self.city = City.objects.create(
            name='Tehran City',
            center=Point(51.38, 35.68, srid=4326)
        )

        # نوع خودرو و نرخ ساعتی
        self.vehicle_type = VehicleType.objects.create(
            name='Sedan',
            base_hourly_rate=50000
        )

        # ================ 2. کاربر کلاینت و پروفایل ================
        self.client_user = User.objects.create_user(
            phone='09121111111',
            role=User.Role.CLIENT
        )
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user,
            full_name='Client Sara',
            national_id='1234567890'
        )
        self.client_api = APIClient()
        self.client_api.force_authenticate(user=self.client_user)

        # ================ 3. کاربر راننده و پروفایل ================
        self.driver_user = User.objects.create_user(
            phone='09122222222',
            role=User.Role.DRIVER
        )
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user,
            full_name='Driver Ali',
            national_id='0987654321'
        )
        self.driver_api = APIClient()
        self.driver_api.force_authenticate(user=self.driver_user)

    def test_full_campaign_to_trip_flow(self):
        # ------------------------------
        # گام ۱: کلاینت یک برند می‌سازد
        # ------------------------------
        brand_response = self.client_api.post('/api/brands/', {
            'name': 'My Brand',
            'slug': 'my-brand'
        })
        self.assertEqual(brand_response.status_code, 201, f"Brand creation failed: {brand_response.data}")
        brand_id = brand_response.data['id']
        print('client crate a brand')
        # ------------------------------
        # گام ۲: کلاینت یک کمپین می‌سازد (با اجزای کامل)
        # ------------------------------
        # فرض می‌کنیم که کمپین از طریق API ساخته می‌شود (اگر endpoint داری،
        # اینجا POST به /api/campaigns/ بزن؛ در غیر این صورت مستقیم مدل را بساز)
        brand_obj = Brand.objects.get(id=brand_id)
        self.campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='My first campaign',
            brand_name=brand_obj,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=10),
            status=Campaign.Status.ACTIVE
        )

        # CampaignSetting
        self.setting = CampaignSetting.objects.create(
            campaign=self.campaign,
            active_days=5,
            activity_hours_per_day='08:00:00',
            max_driver=2,
            vehicle_type=self.vehicle_type
        )

        # CampaignArea – منطقه آزاد با یک پلی‌گون ساده
        poly = Polygon(((51.0, 35.0), (51.0, 36.0), (52.0, 36.0), (52.0, 35.0), (51.0, 35.0)), srid=4326)
        self.area = CampaignArea.objects.create(
            campaign=self.campaign,
            area_type=CampaignArea.AreaType.FREE_AREA,
            city=self.city,
            region_polygon=poly
        )
        print('clients created a campaign')
        # ------------------------------
        # گام ۳: راننده یک خودرو ثبت می‌کند
        # ------------------------------
        vehicle_response = self.driver_api.post('/api/vehicles/', {
            'vehicle_type': self.vehicle_type.id,
            'plate_number': '11B222C33',
            'banner_max_width_cm': 150,
            'banner_max_height_cm': 80
        })
        self.assertEqual(vehicle_response.status_code, 201, f"Vehicle creation failed: {vehicle_response.data}")
        vehicle_id = vehicle_response.data['id']
        vehicle_obj = Vehicle.objects.get(id=vehicle_id)
        print('driver submitted vehicle')

        # ------------------------------
        # گام ۴: راننده کمپین‌های در دسترس را می‌بیند
        # ------------------------------
        available_response = self.driver_api.get(
            f'/api/trips/available-campaigns/?city_id={self.city.id}'
        )
        self.assertEqual(available_response.status_code, 200)
        print('list of available campaigns')
        print(available_response.data, self.campaign.area.city, self.driver_profile)
        self.assertGreaterEqual(len(available_response.data), 1)
        # بررسی اینکه کمپین ما در لیست هست
        campaign_ids = [c['id'] for c in available_response.data]
        self.assertIn(self.campaign.id, campaign_ids)

        # ------------------------------
        # گام ۵: راننده کمپین را انتخاب می‌کند (Trip می‌سازد)
        # ------------------------------
        trip_create_response = self.driver_api.post('/api/trips/', {
            'campaign': self.campaign.id,
            'vehicle': vehicle_id
        })
        print(trip_create_response.data)
        self.assertEqual(trip_create_response.status_code, 201, f"Trip creation failed: {trip_create_response.data}")
        trip_id = trip_create_response.data['id']
        print(trip_id)
        trip = Trip.objects.get(id=trip_id)
        print('trip created and selected')


        # ------------------------------
        # گام ۶: راننده سفر را شروع می‌کند
        # ------------------------------
        start_response = self.driver_api.patch(f'/api/trips/{trip_id}/start/')
        self.assertEqual(start_response.status_code, 200, f"Start failed: {start_response.data}")
        trip.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.ACTIVE)
        self.assertIsNotNone(trip.start_time)

        # ------------------------------
        # گام ۷: راننده چند موقعیت مکانی ارسال می‌کند
        # ------------------------------
        # ارسال موقعیت اول
        location_data1 = {
            "point": {"type": "Point", "coordinates": [51.39, 35.70]}
        }
        loc_resp1 = self.driver_api.post('/api/geo/driver-locations/',
                                         location_data1, format='json')
        self.assertEqual(loc_resp1.status_code, 201)

        # ارسال موقعیت دوم
        location_data2 = {
            "point": {"type": "Point", "coordinates": [51.40, 35.71]}
        }
        loc_resp2 = self.driver_api.post('/api/geo/driver-locations/',
                                         location_data2, format='json')
        self.assertEqual(loc_resp2.status_code, 201)

        # بررسی اینکه موقعیت‌ها به Trip وصل شده‌اند
        self.assertEqual(trip.locations.count(), 2)

        # ------------------------------
        # گام ۸: راننده سفر را پایان می‌دهد
        # ------------------------------
        complete_response = self.driver_api.patch(f'/api/trips/{trip_id}/complete/')
        self.assertEqual(complete_response.status_code, 200, f"Complete failed: {complete_response.data}")
        trip.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.COMPLETED)
        self.assertIsNotNone(trip.end_time)

        # ------------------------------
        # گام ۹: اعتبارسنجی‌های اضافی
        # ------------------------------
        # راننده دیگر نمی‌تواند همزمان دو سفر فعال داشته باشد
        another_vehicle = Vehicle.objects.create(
            driver=self.driver_profile,
            vehicle_type=self.vehicle_type,
            plate_number='99Z999Z99',
            banner_max_width_cm=100,
            banner_max_height_cm=50
        )
        trip2_response = self.driver_api.post('/api/trips/', {
            'campaign': self.campaign.id,
            'vehicle': another_vehicle.id
        })
        # باید موفق باشد چون سفر قبلی تمام شده
        self.assertEqual(trip2_response.status_code, 201)

        # اما همان راننده نمی‌تواند هم‌زمان دو سفر فعال داشته باشد
        # (با شروع سفر جدید و دوباره سعی در ایجاد سفر سوم)
        # اینجا فقط بررسی می‌کنیم که محدودیت یک سفر فعال وجود دارد
        # با شروع سفر دوم و سپس تلاش برای ایجاد سفر سوم
        trip2_id = trip2_response.data['id']
        self.driver_api.patch(f'/api/trips/{trip2_id}/start/')
        trip3_response = self.driver_api.post('/api/trips/', {
            'campaign': self.campaign.id,
            'vehicle': vehicle_obj.id   # خودروی قبلی هنوز فعال است
        })
        # انتظار ۴۰۰ یا ۴۰۳ (بسته به اعتبارسنجی) اما قطعاً نباید ۲۰۱ بدهد
        self.assertNotEqual(trip3_response.status_code, 201,
                            "Should not allow second active trip")

        print("✅ Full integration test passed!")