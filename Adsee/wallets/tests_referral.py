from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta, date
from clients.models import ClientProfile
from drivers.models import DriverProfile
from accounts.models import User
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting
from trips.models import Trip
from wallets.models import Wallet, ReferralReward, Transaction
from support.models import SiteSetting


class ReferralRewardTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='C', national_id='1234567890')
        self.brand = Brand.objects.create(client=self.client_profile, name='B', slug='b')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.campaign = Campaign.objects.create(
            client=self.client_profile, slogan='Test', brand_name=self.brand,
            start_date=date.today(), status=Campaign.Status.ACTIVE
        )
        CampaignSetting.objects.create(campaign=self.campaign, active_days=5, activity_hours_per_day='08:00:00', max_driver=2, vehicle_type=self.vehicle_type)

        # راننده دعوت‌کننده
        self.referrer_user = User.objects.create_user(phone='09120000001', role=User.Role.DRIVER)
        self.referrer = DriverProfile.objects.create(
            user=self.referrer_user, first_name='Referrer', last_name='Test',
            national_id='1111111111', birth_date='1990-01-01',
            referral_code='ABCD1234'
        )
        self.referrer_wallet = Wallet.objects.get(user=self.referrer_user)

        # راننده جدید (دعوت‌شده)
        self.new_driver_user = User.objects.create_user(phone='09120000002', role=User.Role.DRIVER)
        self.new_driver = DriverProfile.objects.create(
            user=self.new_driver_user, first_name='New', last_name='Driver',
            national_id='2222222222', birth_date='1995-01-01',
            referred_by=self.referrer
        )
        self.new_driver_vehicle = Vehicle.objects.create(
            driver=self.new_driver, vehicle_type=self.vehicle_type,
            plate_number='99X999X99', banner_max_width_cm=100, banner_max_height_cm=50
        )

    def test_referral_reward_on_first_trip(self):
        trip = Trip.objects.create(
            driver=self.new_driver,
            campaign=self.campaign,
            vehicle=self.new_driver_vehicle,
            status=Trip.Status.COMPLETED,
            earnings=100000.00,
            start_time=timezone.now() - timedelta(minutes=30),
            end_time=timezone.now()
        )
        # سیگنال باید جایزه را ثبت کرده باشد
        self.assertTrue(ReferralReward.objects.filter(driver=self.referrer).exists())
        reward = ReferralReward.objects.get(driver=self.referrer)
        self.assertEqual(reward.amount, 50000)

        # کیف پول باید افزایش یافته باشد
        self.referrer_wallet.refresh_from_db()
        self.assertEqual(self.referrer_wallet.balance, 50000)

        # تراکنش کیف پول
        tx = Transaction.objects.get(transaction_type='BONUS')
        self.assertEqual(tx.amount, 50000)

    def test_referral_api_apply(self):
        # تست اعمال کد معرف
        fresh_user = User.objects.create_user(phone='09120000003', role=User.Role.DRIVER)
        fresh_driver = DriverProfile.objects.create(
            user=fresh_user,
            first_name='Fresh',
            last_name='Driver',
            national_id='3333333333',
            birth_date='1996-06-06',
            registration_step=4,
            is_contract_accepted=True
            # توجه: referred_by را پر نکنید
        )

        self.client.force_authenticate(user=fresh_user)
        response = self.client.post('/api/drivers/apply-referral/', {
            'referral_code': 'ABCD1234'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        fresh_driver.refresh_from_db()
        self.assertEqual(fresh_driver.referred_by, self.referrer)

    def test_reward_amount_from_site_setting(self):
        setting = SiteSetting.objects.create(
            brand_name='Test',
            referral_reward_amount=75000
        )
        # ساخت اولین سفر برای راننده دعوت‌شده
        trip = Trip.objects.create(
            driver=self.new_driver,
            campaign=self.campaign,
            vehicle=self.new_driver_vehicle,
            status=Trip.Status.COMPLETED,
            earnings=100000.00,
            start_time=timezone.now() - timedelta(minutes=30),
            end_time=timezone.now()
        )
        reward = ReferralReward.objects.get(driver=self.referrer)
        self.assertEqual(reward.amount, 75000)