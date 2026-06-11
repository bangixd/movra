from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from accounts.models import User
from drivers.models import DriverProfile
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting
from geo.models import City
from trips.models import Trip
from django.contrib.gis.geos import Point, Polygon


class TripModelTest(TestCase):
    def setUp(self):
        self.driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
        self.driver = DriverProfile.objects.create(user=self.driver_user, full_name='Ali', national_id='1111111111')
        self.other_driver_user = User.objects.create_user(phone='09123333333', role=User.Role.DRIVER)
        self.other_driver = DriverProfile.objects.create(user=self.other_driver_user, full_name='Hossein', national_id='2222222222')

        self.client_user = User.objects.create_user(phone='09124444444', role=User.Role.CLIENT)
        self.client = ClientProfile.objects.create(user=self.client_user, full_name='Sara', national_id='3333333333')
        self.brand = Brand.objects.create(client=self.client, name='Brand1', slug='brand1')
        self.campaign = Campaign.objects.create(
            client=self.client, slogan='Camp1', brand_name=self.brand,
            start_date=timezone.datetime.today(), end_date=timezone.datetime.today() + timedelta(days=5)
        )
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.vehicle = Vehicle.objects.create(
            driver=self.driver, vehicle_type=self.vehicle_type,
            plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50
        )
        self.vehicle2 = Vehicle.objects.create(
            driver=self.other_driver, vehicle_type=self.vehicle_type,
            plate_number='98X765Y43', banner_max_width_cm=100, banner_max_height_cm=50
        )
        # 🔧 ساخت CampaignSetting و تزریق مستقیم به campaign برای تست clean
        self.campaign_setting = CampaignSetting.objects.create(
            campaign=self.campaign, active_days=5,
            activity_hours_per_day='08:00:00', max_driver=2,
            vehicle_type=self.vehicle_type
        )
        # ⚠️ با این کار campaign.setting به این آبجکت اشاره می‌کند (دور زدن مشکل FK)
        self.campaign.setting = self.campaign_setting

    def test_create_trip_with_valid_constraints(self):
        trip = Trip.objects.create(
            driver=self.driver, campaign=self.campaign, vehicle=self.vehicle
        )
        self.assertEqual(trip.status, Trip.Status.PENDING)
        self.assertIsNotNone(trip.snapshot)

    def test_vehicle_must_belong_to_driver(self):
        with self.assertRaises(Exception):
            Trip.objects.create(driver=self.driver, campaign=self.campaign, vehicle=self.vehicle2)

    def test_only_one_active_trip(self):
        Trip.objects.create(driver=self.driver, campaign=self.campaign, vehicle=self.vehicle, status=Trip.Status.ACTIVE)
        with self.assertRaises(Exception):
            Trip.objects.create(driver=self.driver, campaign=self.campaign, vehicle=self.vehicle, status=Trip.Status.ACTIVE)

    def test_max_drivers_limit(self):
        # پر کردن ظرفیت با دو راننده
        Trip.objects.create(driver=self.driver, campaign=self.campaign, vehicle=self.vehicle, status=Trip.Status.ACTIVE)
        Trip.objects.create(driver=self.other_driver, campaign=self.campaign, vehicle=self.vehicle2, status=Trip.Status.ACTIVE)
        third_driver_user = User.objects.create_user(phone='09125555555', role=User.Role.DRIVER)
        third_driver = DriverProfile.objects.create(user=third_driver_user, full_name='Third', national_id='5555555555')
        third_vehicle = Vehicle.objects.create(
            driver=third_driver, vehicle_type=self.vehicle_type,
            plate_number='11C444D55', banner_max_width_cm=100, banner_max_height_cm=50
        )
        with self.assertRaises(Exception):
            Trip.objects.create(driver=third_driver, campaign=self.campaign, vehicle=third_vehicle, status=Trip.Status.ACTIVE)


class TripAPITest(TestCase):
    def setUp(self):
        # ساخت داده‌های مشابه بالا
        self.driver_user = User.objects.create_user(phone='09126666666', role=User.Role.DRIVER)
        self.driver = DriverProfile.objects.create(user=self.driver_user, full_name='TestDriver', national_id='8888888888')
        self.client_user = User.objects.create_user(phone='09127777777', role=User.Role.CLIENT)
        self.client = ClientProfile.objects.create(user=self.client_user, full_name='TestClient', national_id='7777777777')
        self.brand = Brand.objects.create(client=self.client, name='TestBrand', slug='testbrand')
        self.campaign = Campaign.objects.create(
            client=self.client, slogan='TestCamp', brand_name=self.brand,
            start_date=date.today(), end_date=date.today() + timedelta(days=5),
            status=Campaign.Status.ACTIVE
        )
        self.vehicle_type = VehicleType.objects.create(name='SUV', base_hourly_rate=80000)
        self.vehicle = Vehicle.objects.create(
            driver=self.driver, vehicle_type=self.vehicle_type,
            plate_number='66M777N88', banner_max_width_cm=200, banner_max_height_cm=100
        )
        self.campaign_setting = CampaignSetting.objects.create(
            campaign=self.campaign, active_days=5,
            activity_hours_per_day='08:00:00', max_driver=2,
            vehicle_type=self.vehicle_type
        )
        # 🔧 باز هم campaign.setting را تزریق می‌کنیم
        self.campaign.setting = self.campaign_setting

        # 🔧 شهر با مرکز معتبر
        self.city = City.objects.create(
            name='Tehran',
            center=Point(51.38, 35.68, srid=4326)   # مختصات الزامی است
        )

        self.api = APIClient()
        self.api.force_authenticate(user=self.driver_user)

    def test_create_trip(self):
        response = self.api.post('/v1/trips/', {
            'campaign': self.campaign.id,
            'vehicle': self.vehicle.id
        }, format='json')
        self.assertEqual(response.status_code, 201)
        trip = Trip.objects.get()
        self.assertEqual(trip.status, Trip.Status.PENDING)

    def test_start_trip(self):
        trip = Trip.objects.create(driver=self.driver, campaign=self.campaign, vehicle=self.vehicle)
        response = self.api.patch(f'/v1/trips/{trip.id}/start/')
        self.assertEqual(response.status_code, 200)
        trip.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.ACTIVE)

    def test_available_campaigns_city_filter(self):
        # یک CampaignArea برای کمپین می‌سازیم
        from campaigns.models import CampaignArea
        CampaignArea.objects.create(
            campaign=self.campaign,
            area_type=CampaignArea.AreaType.FREE_AREA,
            city=self.city,
            region_polygon=Polygon(((0,0), (0,1), (1,1), (1,0), (0,0)), srid=4326)
        )
        response = self.api.get(f'/v1/trips/available-campaigns/?city_id={self.city.id}')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.campaign.id)