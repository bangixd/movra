from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from django.contrib.gis.geos import Point
from accounts.models import User
from drivers.models import DriverProfile
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting
from geo.models import DriverLocation, City
from trips.models import Trip

class BatchLocationTest(TestCase):
    def setUp(self):
        print("\n========== BATCH LOCATION SETUP ==========")
        # کاربر راننده
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(user=self.driver_user, full_name='Ali', national_id='1234567890')
        # کلاینت و کمپین
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='Sara', national_id='1111111111')
        self.brand = Brand.objects.create(client=self.client_profile, name='B', slug='b')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.campaign = Campaign.objects.create(
            client=self.client_profile, slogan='Test', brand_name=self.brand,
            start_date='2026-01-01', end_date='2026-01-10', status=Campaign.Status.ACTIVE
        )
        self.campaign_setting = CampaignSetting.objects.create(
            campaign=self.campaign, active_days=5, activity_hours_per_day='08:00:00', max_driver=2, vehicle_type=self.vehicle_type
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver_profile, vehicle_type=self.vehicle_type,
            plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50
        )
        self.trip = Trip.objects.create(
            driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
            status=Trip.Status.ACTIVE, start_time=timezone.now()
        )
        self.api = APIClient()
        self.api.force_authenticate(user=self.driver_user)
        print("✅ Setup complete")

    def test_batch_upload_success(self):
        print("\n--- TEST: Batch Upload Success ---")
        response = self.api.post('/api/geo/driver-locations/batch/', {
            'trip_id': self.trip.id,
            'points': [
                {'lat': 35.70, 'lon': 51.39, 'timestamp': 1715172000, 'speed': 40, 'heading': 90},
                {'lat': 35.71, 'lon': 51.40, 'timestamp': 1715172060, 'speed': 45, 'heading': 95},
            ]
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(DriverLocation.objects.count(), 2)
        # بررسی source
        for loc in DriverLocation.objects.all():
            self.assertEqual(loc.source, 'batch')
        print("✅ Batch uploaded, source='batch' verified")

    def test_batch_locations_have_source_batch(self):
        print("\n--- TEST: Batch Locations Have source='batch' ---")
        self.api.post('/api/geo/driver-locations/batch/', {
            'trip_id': self.trip.id,
            'points': [{'lat': 35.70, 'lon': 51.39, 'timestamp': 1715172000}]
        }, format='json')
        loc = DriverLocation.objects.last()
        self.assertEqual(loc.source, 'batch')
        print("✅ source='batch' confirmed")

    def test_realtime_location_has_source_realtime(self):
        print("\n--- TEST: Realtime Location Has source='realtime' ---")
        loc = DriverLocation.objects.create(
            driver=self.driver_user,
            trip=self.trip,
            point=Point(51.39, 35.70, srid=4326)
        )
        self.assertEqual(loc.source, 'realtime')
        print("✅ source='realtime' confirmed")

    def test_batch_requires_active_trip(self):
        print("\n--- TEST: Batch Requires Active Trip ---")
        # پایان سفر
        self.trip.status = Trip.Status.COMPLETED
        self.trip.save()
        response = self.api.post('/api/geo/driver-locations/batch/', {
            'trip_id': self.trip.id,
            'points': [{'lat': 35.70, 'lon': 51.39, 'timestamp': 1715172000}]
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Trip is not active", response.data['error'])
        print("✅ Non-active trip rejected")