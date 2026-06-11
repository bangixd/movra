# trips/tests_rating.py
from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta, date
from accounts.models import User
from drivers.models import DriverProfile
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting
from trips.models import Trip

class DriverRatingTest(TestCase):
    def setUp(self):
        # مشتری
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='Client', national_id='1234567890')
        self.brand = Brand.objects.create(client=self.client_profile, name='B', slug='b')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.campaign = Campaign.objects.create(client=self.client_profile, slogan='C', brand_name=self.brand, start_date=date.today(), status=Campaign.Status.ACTIVE)
        CampaignSetting.objects.create(campaign=self.campaign, active_days=5, activity_hours_per_day='08:00:00', max_driver=1, vehicle_type=self.vehicle_type)

        # راننده
        self.driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user, full_name='Ali Rezaei',
            national_id='1234567890', birth_date='1990-01-01'
        )
        self.vehicle = Vehicle.objects.create(driver=self.driver_profile, vehicle_type=self.vehicle_type, plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50)

        # سفر تکمیل‌شده
        self.trip = Trip.objects.create(
            driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
            status=Trip.Status.COMPLETED, start_time=timezone.now()-timedelta(hours=1), end_time=timezone.now()
        )
        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)

    def test_rate_driver(self):
        response = self.api.post(f'/v1/trips/{self.trip.id}/rate/', {
            'rating': 4,
            'feedback': 'عالی بود'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.rating, 4)
        self.driver_profile.refresh_from_db()
        self.assertEqual(self.driver_profile.average_rating, 4.0)
        self.assertEqual(self.driver_profile.total_ratings, 1)

    def test_rating_updates_average(self):
        # امتیاز اول
        self.api.post(f'/v1/trips/{self.trip.id}/rate/', {'rating': 5}, format='json')
        # سفر دوم
        trip2 = Trip.objects.create(
            driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
            status=Trip.Status.COMPLETED, start_time=timezone.now(), end_time=timezone.now()
        )
        self.api.post(f'/v1/trips/{trip2.id}/rate/', {'rating': 3}, format='json')
        self.driver_profile.refresh_from_db()
        self.assertEqual(self.driver_profile.average_rating, 4.0)  # (5+3)/2 = 4.0
        self.assertEqual(self.driver_profile.total_ratings, 2)

    def test_invalid_rating(self):
        response = self.api.post(f'/v1/trips/{self.trip.id}/rate/', {'rating': 6}, format='json')
        self.assertEqual(response.status_code, 400)