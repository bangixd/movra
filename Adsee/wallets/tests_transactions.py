from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from clients.models import ClientProfile
from drivers.models import DriverProfile
from accounts.models import User
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting
from trips.models import Trip
from wallets.models import Wallet, Transaction, BankAccount

class WalletAPITest(TestCase):
    def setUp(self):
        # راننده و کیف پول
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user, first_name='Ali', last_name='Rezaei',
            national_id='1234567890', birth_date='1990-01-01',
            registration_step=4, is_contract_accepted=True
        )
        self.wallet = Wallet.objects.get(user=self.driver_user)

        # ساخت یک کمپین و سفر برای تست درآمد
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='C', national_id='1234567890')
        self.brand = Brand.objects.create(client=self.client_profile, name='B', slug='b')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.campaign = Campaign.objects.create(
            client=self.client_profile, slogan='Test', brand_name=self.brand,
            start_date=date.today(), status=Campaign.Status.ACTIVE
        )
        CampaignSetting.objects.create(campaign=self.campaign, active_days=5, activity_hours_per_day='08:00:00', max_driver=2, vehicle_type=self.vehicle_type)
        self.vehicle = Vehicle.objects.create(driver=self.driver_profile, vehicle_type=self.vehicle_type, plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50)

        self.trip = Trip.objects.create(
            driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
            status=Trip.Status.COMPLETED, earnings=125000.00,
            start_time=timezone.now() - timedelta(minutes=30), end_time=timezone.now()
        )
        # سیگنال باید تراکنش درآمد بسازد
        self.income_tx = Transaction.objects.get(trip=self.trip)

        # API client
        self.api = APIClient()
        self.api.force_authenticate(user=self.driver_user)

    def test_wallet_summary(self):
        response = self.api.get('/api/wallets/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_earnings'], '125000.00')
        self.assertEqual(response.data['balance'], '125000.00')

    def test_transaction_list(self):
        response = self.api.get('/api/wallets/transactions/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['amount'], '125000.00')

    def test_bank_account_creation(self):
        response = self.api.post('/api/wallets/bank/', {
            'card_number': '6037997512345678',
            'sheba_number': 'IR123456789012345678901234',
            'bank_name': 'ملی'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(BankAccount.objects.filter(driver=self.driver_profile).exists())