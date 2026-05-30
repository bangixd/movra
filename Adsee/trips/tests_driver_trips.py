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
from trips.models import Trip, TripAnalysis
from wallets.models import Wallet, Transaction
from decimal import Decimal


class DriverTripAPITest(TestCase):
    def setUp(self):
        # ساخت راننده
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user, full_name='Ali Rezaei',
            national_id='1234567890', birth_date='1990-01-01',
            registration_step=4, is_contract_accepted=True
        )
        # ساخت کلاینت و کمپین
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='C', national_id='1234567890')
        self.brand = Brand.objects.create(client=self.client_profile, name='TestBrand', slug='test-brand')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.vehicle = Vehicle.objects.create(driver=self.driver_profile, vehicle_type=self.vehicle_type, plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50)
        self.campaign = Campaign.objects.create(
            client=self.client_profile, slogan='TestCamp', brand_name=self.brand,
            start_date=date.today(), end_date=date.today() + timedelta(days=5),
            status=Campaign.Status.ACTIVE
        )
        CampaignSetting.objects.create(
            campaign=self.campaign, active_days=5, activity_hours_per_day='08:00:00',
            max_driver=3, vehicle_type=self.vehicle_type
        )
        # ساخت دو سفر با وضعیت‌های مختلف
        self.active_trip = Trip.objects.create(
            driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
            status=Trip.Status.ACTIVE,
            start_time=timezone.now() - timedelta(hours=2)
        )
        self.completed_trip = Trip.objects.create(
            driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
            status=Trip.Status.COMPLETED,
            start_time=timezone.now() - timedelta(days=1, hours=5),
            end_time=timezone.now() - timedelta(days=1),
            earnings=125000.00
        )
        # کیف پول و تراکنش
        self.wallet = Wallet.objects.get(user=self.driver_user)
        self.tx = Transaction.objects.create(
            wallet=self.wallet,
            amount=125000.00,
            transaction_type='INCOME',
            status='SUCCESS',
            trip=self.completed_trip
        )
        # تحلیل برای سفر کامل‌شده
        self.analysis = TripAnalysis.objects.create(
            trip=self.completed_trip,
            distance_km=15.5,
            raw_response={
                'night_income_factor': 0.9,
                'long_stop_income_factor': 0.95,
                'suspicious_stop_penalty_factor': 0.7,
                'invalid_data_penalty_factor': 0.25,
                'total_penalty_amount': 5000
            }
        )

        self.api = APIClient()
        self.api.force_authenticate(user=self.driver_user)

    def test_list_trips_filter_by_status(self):
        response = self.api.get('/api/trips/?status=ACTIVE')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'ACTIVE')

    def test_trip_detail_active(self):
        response = self.api.get(f'/api/trips/{self.active_trip.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ACTIVE')
        self.assertIn('brand_name', response.data)
        self.assertIn('remaining_days', response.data)
        self.assertIn('remaining_hours', response.data)

    def test_trip_detail_completed(self):
        response = self.api.get(f'/api/trips/{self.completed_trip.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['paid_amount'], Decimal('125000.00'))
        self.assertIn('deductions', response.data)
        self.assertEqual(response.data['distance_km'], 15.5)

    def test_deductions_in_completed_trip(self):
        response = self.api.get(f'/api/trips/{self.completed_trip.id}/')
        self.assertEqual(response.status_code, 200)
        deductions = response.data['deductions']
        self.assertIn('night_factor', deductions)
        self.assertIn('long_stop_factor', deductions)
        # بسته به دادهٔ mock شده
        self.assertAlmostEqual(deductions['night_factor'], 0.9)
