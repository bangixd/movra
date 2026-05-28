from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from clients.models import ClientProfile
from drivers.models import DriverProfile
from accounts.models import User
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting, CampaignArea
from geo.models import City
from trips.models import Trip, TripAnalysis
from wallets.models import Wallet
import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.gis.geos import Point

class DriverHomeTest(TestCase):
    def setUp(self):
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user, first_name='Ali', last_name='Rezaei',
            national_id='1234567890', birth_date='1990-01-01',
            registration_step=4, is_contract_accepted=True
        )
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='C', national_id='1234567890')
        self.brand = Brand.objects.create(client=self.client_profile, name='B', slug='b')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.vehicle = Vehicle.objects.create(driver=self.driver_profile, vehicle_type=self.vehicle_type, plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50)
        self.city = City.objects.create(name='Tehran', center=Point(51.38, 35.68, srid=4326))
        self.campaign = Campaign.objects.create(
            client=self.client_profile, slogan='Test', brand_name=self.brand,
            start_date=date.today(), end_date=date.today() + timedelta(days=5),
            status=Campaign.Status.ACTIVE
        )
        CampaignSetting.objects.create(campaign=self.campaign, active_days=5, activity_hours_per_day='08:00:00', max_driver=2, vehicle_type=self.vehicle_type)
        CampaignArea.objects.create(campaign=self.campaign, area_type=CampaignArea.AreaType.CIRCLE, city=self.city)
        self.api = APIClient()
        self.api.force_authenticate(user=self.driver_user)

    def test_home_without_active_trip(self):
        response = self.api.get('/api/trips/home/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'no_active_trip')
        self.assertIn('available_campaigns', response.data)

    def test_home_with_active_trip(self):
        trip = Trip.objects.create(
            driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
            status=Trip.Status.ACTIVE, start_time=timezone.now()
        )
        response = self.api.get('/api/trips/home/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'active_trip')
        self.assertIn('active_trip', response.data)
        self.assertEqual(response.data['active_trip']['id'], trip.id)

    def test_upload_installation(self):
        trip = Trip.objects.create(driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
                                   status=Trip.Status.PENDING)

        # ساخت یک تصویر PNG معتبر (۱×۱ پیکسل)
        image = Image.new('RGB', (1, 1), color='red')
        buf = io.BytesIO()
        image.save(buf, 'PNG')
        buf.seek(0)
        sticker = SimpleUploadedFile("sticker.png", buf.read(), content_type="image/png")
        # برای عکس دوم نیز همان تصویر را با نامی دیگر دوباره می‌خوانیم
        buf.seek(0)
        driver_photo = SimpleUploadedFile("driver.png", buf.read(), content_type="image/png")

        response = self.api.patch(
            f'/api/trips/{trip.id}/upload-installation/',
            {'sticker_image': sticker, 'driver_car_image': driver_photo},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        trip.refresh_from_db()
        self.assertTrue(trip.installation_verified)