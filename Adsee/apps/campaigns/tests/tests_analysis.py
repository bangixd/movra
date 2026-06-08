from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from accounts.models import User
from clients.models import ClientProfile
from drivers.models import DriverProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting
from trips.models import Trip, TripAnalysis

class CampaignAnalysisCSVTest(TestCase):
    def setUp(self):
        print("\n========== CAMPAIGN ANALYSIS CSV SETUP ==========")
        # کلاینت اصلی (مالک کمپین)
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='Client Sara', national_id='1234567890')
        self.client_api = APIClient()
        self.client_api.force_authenticate(user=self.client_user)

        # کلاینت دیگر (بدون دسترسی)
        self.other_client_user = User.objects.create_user(phone='09120000000', role=User.Role.CLIENT)
        self.other_client_profile = ClientProfile.objects.create(user=self.other_client_user, full_name='Other', national_id='1111111111')
        self.other_client_api = APIClient()
        self.other_client_api.force_authenticate(user=self.other_client_user)

        # برند و نوع خودرو و کمپین
        self.brand = Brand.objects.create(client=self.client_profile, name='BrandX', slug='brandx')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.campaign = Campaign.objects.create(
            client=self.client_profile, slogan='Campaign A', brand_name=self.brand,
            start_date=date.today(), end_date=date.today() + timedelta(days=5),
            status=Campaign.Status.ACTIVE
        )
        self.campaign_setting = CampaignSetting.objects.create(
            campaign=self.campaign, active_days=5, activity_hours_per_day='08:00:00',
            max_driver=3, vehicle_type=self.vehicle_type
        )

        # راننده و خودرو
        self.driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user,
            full_name='Driver Ali',
            national_id='0987654321',
            birth_date='1990-01-01',
            registration_step=4,
            is_contract_accepted=True
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver_profile, vehicle_type=self.vehicle_type,
            plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50
        )

        # ساخت یک سفر کامل‌شده با تحلیل
        self.trip = Trip.objects.create(
            driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
            status=Trip.Status.COMPLETED,
            start_time=timezone.now() - timedelta(minutes=20),
            end_time=timezone.now(),
            earnings=125000.00
        )
        self.analysis = TripAnalysis.objects.create(
            trip=self.trip,
            active_seconds=1200, distance_km=8.5, exposure_score=0.88,
            estimated_impressions=1500, data_quality=0.95, confidence=0.9,
            avg_traffic_ratio=1.2, analysis_run_id='run-001'
        )

        print("✅ Setup complete")

    def test_csv_download_by_campaign_owner(self):
        print("\n--- TEST: CSV download by campaign owner ---")
        response = self.client_api.get(f'/v1/campaigns/{self.campaign.id}/analysis/csv/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')  # BOM برداشته می‌شود
        self.assertIn('شناسه سفر', content)
        self.assertIn('Ali', content)            # نام راننده
        self.assertIn('12A345B67', content)      # پلاک
        self.assertIn('125000.00', content)      # درآمد
        self.assertIn('1500', content)           # تخمین مشاهده
        print("✅ CSV contains correct data")

    def test_csv_access_denied_for_other_client(self):
        print("\n--- TEST: CSV access denied for other client ---")
        response = self.other_client_api.get(f'/v1/campaigns/{self.campaign.id}/analysis/csv/')
        self.assertEqual(response.status_code, 403)
        print("✅ Access denied for non-owner")

    def test_csv_no_completed_trips(self):
        print("\n--- TEST: CSV when no completed trips ---")
        # حذف تحلیل و تغییر وضعیت سفر
        self.analysis.delete()
        self.trip.status = Trip.Status.CANCELLED
        self.trip.save()
        response = self.client_api.get(f'/v1/campaigns/{self.campaign.id}/analysis/csv/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        # فقط هدر وجود دارد و سطری برای داده نیست
        lines = content.strip().split('\n')
        self.assertEqual(len(lines), 1)  # فقط هدر
        print("✅ Empty CSV returned")