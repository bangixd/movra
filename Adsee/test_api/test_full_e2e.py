from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.gis.geos import Point, Polygon

from accounts.models import User
from drivers.models import DriverProfile, DriverDocument
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import (
    Campaign, CampaignSetting, CampaignDesign, CampaignArea,
    CampaignInvoice, PaymentTransaction, CampaignPricingRule
)
from geo.models import City, Province
from trips.models import Trip, TripAnalysis
from wallets.models import Wallet, Transaction as WalletTransaction
from notifications.models import Notification
from print_shops.models import PrintShopProfile


class FullE2ETest(TestCase):
    def setUp(self):
        # ========== داده‌های پایه ==========
        self.province = Province.objects.create(name='تهران')
        self.city = City.objects.create(
            name='تهران',
            province=self.province,
            center=Point(51.38, 35.68, srid=4326)
        )
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)

        # ========== کاربران ==========
        # مشتری
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user,
            full_name='مشتری تست',
            national_id='1234567890',
            advertiser_type=ClientProfile.AdvertiserType.REAL
        )
        # راننده (با full_name)
        self.driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user,
            full_name='راننده تستی',
            registration_step=DriverProfile.RegistrationStep.PERSONAL_INFO
        )
        # ادمین
        self.admin_user = User.objects.create_superuser(phone='09990000000', password='admin')

        # ========== API Clients ==========
        self.client_api = APIClient()
        self.client_api.force_authenticate(user=self.client_user)

        self.driver_api = APIClient()
        self.driver_api.force_authenticate(user=self.driver_user)

        self.admin_api = APIClient()
        self.admin_api.force_authenticate(user=self.admin_user)

        # ========== پیکربندی قوانین قیمت‌گذاری (برای محاسبه هزینه) ==========
        # برای سادگی، یک قانون پایه می‌سازیم تا calculate_campaign_cost مقادیر مثبت برگرداند
        CampaignPricingRule.objects.create(
            key='DRIVER_COST_PER_DAY',
            title='هزینه روزانه راننده',
            value_type=CampaignPricingRule.ValueType.DECIMAL,
            decimal_value=Decimal('200000')
        )
        CampaignPricingRule.objects.create(
            key='DESIGN_COST_USER_UPLOAD',
            title='هزینه طراحی آپلود کاربر',
            value_type=CampaignPricingRule.ValueType.DECIMAL,
            decimal_value=Decimal('50000')
        )
        CampaignPricingRule.objects.create(
            key='AREA_COST_FREE',
            title='هزینه منطقه آزاد',
            value_type=CampaignPricingRule.ValueType.DECIMAL,
            decimal_value=Decimal('100000')
        )
        CampaignPricingRule.objects.create(
            key='TAX_RATE',
            title='نرخ مالیات',
            value_type=CampaignPricingRule.ValueType.DECIMAL,
            decimal_value=Decimal('0.09')
        )

    # ------------------------------------------------------------------
    @patch('services.payment_gateway.ZarinpalGateway.send_request')
    @patch('services.analytics_client.AnalyticsServiceClient.register_vehicle')
    @patch('services.analytics_client.AnalyticsServiceClient.send_single_location')
    @patch('services.analytics_client.AnalyticsServiceClient.calculate_earnings')
    @patch('services.analytics_client.AnalyticsServiceClient.get_analysis_summary')
    @patch('services.analytics_client.AnalyticsServiceClient.create_analysis_run')
    @patch('services.tasks.update_earnings_task.delay')          # جلوگیری از ارسال واقعی به Celery
    @patch('services.tasks.fetch_and_store_trip_analysis.delay') # جلوگیری از ارسال واقعی به Celery
    def test_full_e2e_flow(
        self,
        mock_fetch_analysis_delay,
        mock_update_earnings_delay,
        mock_create_run,
        mock_get_summary,
        mock_calc_earnings,
        mock_send_location,
        mock_register_vehicle,
        mock_zarinpal
    ):
        # ========== پیکربندی Mockها ==========
        mock_zarinpal.return_value = (True, 'https://sandbox.zarinpal.com/pg/StartPay/ABC123', None)
        mock_register_vehicle.return_value = {"status": "ok"}
        mock_send_location.return_value = {"status": "ok"}
        mock_calc_earnings.return_value = {"earnings": 150000.00}
        mock_get_summary.return_value = {
            'active_seconds': 600,
            'distance_km': 5.0,
            'exposure_score': 0.85,
            'estimated_impressions': 1200,
            'data_quality': 0.95,
            'confidence': 0.9,
            'avg_traffic_ratio': 1.2
        }
        mock_create_run.return_value = {'run_id': 'run-001'}

        # ================================================================
        # 1. مشتری برند می‌سازد
        # ================================================================
        resp = self.client_api.post('/api/brands/', {
            'name': 'برند تست',
            'slug': 'test-brand'
        })
        self.assertEqual(resp.status_code, 201)
        brand_id = resp.data['id']
        brand = Brand.objects.get(id=brand_id)

        # ================================================================
        # 2. مشتری کمپین می‌سازد (همراه تنظیمات، طراحی، محدوده)
        # ================================================================
        # 2.1 کمپین
        resp = self.client_api.post('/api/campaigns/', {
            'client': self.client_profile.id,
            'slogan': 'کمپین تست',
            'brand_name': brand.id,
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=10)),
            'status': Campaign.Status.DRAFT
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        campaign_id = resp.data['id']
        campaign = Campaign.objects.get(id=campaign_id)

        # 2.2 تنظیمات
        CampaignSetting.objects.create(
            campaign=campaign,
            active_days=5,
            activity_hours_per_day='08:00:00',
            max_driver=2,
            vehicle_type=self.vehicle_type
        )

        # 2.3 طراحی (استفاده از قالب پیش‌فرض یا آپلود کاربر)
        design = CampaignDesign.objects.create(
            campaign=campaign,
            design_type=CampaignDesign.DesignType.USER_UPLOAD,
            status=CampaignDesign.DesignStatus.COMPLETED
        )

        # 2.4 محدوده
        poly = Polygon(((51.0, 35.0), (51.0, 36.0), (52.0, 36.0), (52.0, 35.0), (51.0, 35.0)), srid=4326)
        CampaignArea.objects.create(
            campaign=campaign,
            area_type=CampaignArea.AreaType.FREE_AREA,
            city=self.city,
            region_polygon=poly
        )

        # فعال‌سازی کمپین (از طریق پرداخت فرضی)
        campaign.status = Campaign.Status.ACTIVE
        campaign.save()

        # ================================================================
        # 3. راننده پروفایل خود را تکمیل می‌کند (مرحله ۱) – با full_name
        # ================================================================
        resp = self.driver_api.patch(f'/api/drivers/profiles/{self.driver_profile.id}/', {
            'full_name': 'علی رضایی',
            'national_id': '1234567890',
            'birth_date': '1990-01-01',
            'city': self.city.id
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.driver_profile.refresh_from_db()
        self.assertEqual(self.driver_profile.registration_step, DriverProfile.RegistrationStep.DOCUMENTS)

        # ================================================================
        # 4. راننده مدارک را آپلود می‌کند (مرحله ۲)
        # ================================================================
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_file = SimpleUploadedFile("doc.jpg", b"file_content", content_type="image/jpeg")
        resp = self.driver_api.post(f'/api/drivers/documents/', {
            'document_type': 'DRIVING_LICENSE',
            'file': fake_file
        }, format='multipart')
        print("Request URL:", resp.request['PATH_INFO'])
        print("Status:", resp.status_code)
        print("Data:", resp.data)
        self.assertEqual(resp.status_code, 201)
        self.driver_profile.refresh_from_db()
        self.assertEqual(self.driver_profile.registration_step, DriverProfile.RegistrationStep.VERIFICATION)

        # ================================================================
        # 5. ادمین مدارک را تأیید می‌کند (مرحله ۳)
        # ================================================================
        doc = DriverDocument.objects.first()
        resp = self.admin_api.patch(f'/api/drivers/documents/{doc.id}/review/', {
            'status': 'APPROVED'
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.driver_profile.refresh_from_db()
        self.assertEqual(self.driver_profile.kyc_status, 'APPROVED')
        self.assertEqual(self.driver_profile.registration_step, DriverProfile.RegistrationStep.CONTRACT)

        # ================================================================
        # 6. راننده قرارداد را می‌پذیرد (مرحله ۴)
        # ================================================================
        resp = self.driver_api.patch('/api/drivers/profiles/accept_contract/')
        self.assertEqual(resp.status_code, 200)
        self.driver_profile.refresh_from_db()
        self.assertTrue(self.driver_profile.is_contract_accepted)

        # ================================================================
        # 7. راننده خودرو ثبت می‌کند
        # ================================================================
        resp = self.driver_api.post('/api/vehicles/', {
            'vehicle_type': self.vehicle_type.id,
            'plate_number': '12A345B67',
            'banner_max_width_cm': 150,
            'banner_max_height_cm': 80
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        vehicle_id = resp.data['id']
        vehicle = Vehicle.objects.get(id=vehicle_id)

        # ================================================================
        # 8. راننده کمپین‌های در دسترس را می‌بیند
        # ================================================================
        resp = self.driver_api.get(f'/api/trips/available-campaigns/?city_id={self.city.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.data), 0)
        self.assertIn(campaign.id, [c['id'] for c in resp.data])

        # ================================================================
        # 9. راننده یک Trip ایجاد می‌کند (انتخاب کمپین)
        # ================================================================
        resp = self.driver_api.post('/api/trips/', {
            'campaign': campaign.id,
            'vehicle': vehicle.id
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        trip_id = resp.data['id']
        trip = Trip.objects.get(id=trip_id)

        # ================================================================
        # 10. شروع سفر
        # ================================================================
        resp = self.driver_api.patch(f'/api/trips/{trip_id}/start/')
        self.assertEqual(resp.status_code, 200)
        trip.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.ACTIVE)
        self.assertIsNotNone(trip.start_time)

        # ================================================================
        # 11. ارسال موقعیت‌های مکانی (هم realtime و هم batch)
        # ================================================================
        # realtime
        loc1 = self.driver_api.post('/api/geo/driver-locations/', {
            'point': {'type': 'Point', 'coordinates': [51.39, 35.70]}
        }, format='json')
        self.assertEqual(loc1.status_code, 201)

        # batch
        resp = self.driver_api.post('/api/geo/driver-locations/batch/', {
            'trip_id': trip_id,
            'points': [
                {'lat': 35.71, 'lon': 51.40, 'timestamp': int(timezone.now().timestamp())},
                {'lat': 35.72, 'lon': 51.41, 'timestamp': int(timezone.now().timestamp())},
            ]
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(trip.locations.count(), 3)  # 1 realtime + 2 batch

        # ================================================================
        # 12. پایان سفر
        # ================================================================
        resp = self.driver_api.patch(f'/api/trips/{trip_id}/complete/')
        self.assertEqual(resp.status_code, 200)
        trip.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.COMPLETED)
        self.assertIsNotNone(trip.end_time)

        # ================================================================
        # 13. بررسی درآمد (از آنجایی که تسک Celery را mock کردیم،
        #     earnings را دستی برابر با مقدار mock قرار می‌دهیم)
        trip.earnings = 150000.00
        trip.save()

        # ================================================================
        # 14. ذخیره تحلیل سفر (شبیه‌سازی فراخوانی تسک)
        # ================================================================
        TripAnalysis.objects.create(
            trip=trip,
            active_seconds=600,
            distance_km=5.0,
            exposure_score=0.85,
            estimated_impressions=1200,
            analysis_run_id='run-001'
        )

        # ================================================================
        # 15. راننده کیف پول و تراکنش‌ها را می‌بیند
        # ================================================================
        wallet = Wallet.objects.get(user=self.driver_user)
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=Decimal(150000.00),
            transaction_type=WalletTransaction.TransactionType.INCOME,
            status=WalletTransaction.Status.SUCCESS,
            description='درآمد سفر',
            trip=trip
        )
        wallet.balance = Decimal(150000.00)
        wallet.total_earnings = Decimal(150000.00)
        wallet.save()

        resp = self.driver_api.get('/api/wallets/summary/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Decimal(resp.data['balance']), Decimal('150000.00'))

        # ================================================================
        # 16. مشتری گزارش CSV کمپین را دانلود می‌کند
        # ================================================================
        resp = self.client_api.get(f'/api/campaigns/{campaign.id}/analysis/csv/')
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8-sig')
        self.assertIn('راننده', content)

        print("✅ تمام مراحل E2E با موفقیت پاس شد.")