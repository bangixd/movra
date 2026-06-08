from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from accounts.models import User
from drivers.models import DriverProfile
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting, CampaignInvoice
from trips.models import Trip, TripAnalysis

class ClientReportTest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='C', national_id='1234567890')
        self.brand = Brand.objects.create(client=self.client_profile, name='B', slug='b')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.campaign = Campaign.objects.create(
            client=self.client_profile, slogan='Test', brand_name=self.brand,
            start_date=date.today(), status=Campaign.Status.ACTIVE
        )
        CampaignSetting.objects.create(campaign=self.campaign, active_days=5, activity_hours_per_day='08:00:00', max_driver=1, vehicle_type=self.vehicle_type)
        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)

    def test_report_summary(self):
        # ساخت یک سفر کامل‌شده با تحلیل
        driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
        driver_profile = DriverProfile.objects.create(user=driver_user, full_name='D', national_id='0987654321')
        vehicle = Vehicle.objects.create(driver=driver_profile, vehicle_type=self.vehicle_type, plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50)
        trip = Trip.objects.create(driver=driver_profile, campaign=self.campaign, vehicle=vehicle, status='COMPLETED', start_time=timezone.now()-timedelta(hours=1), end_time=timezone.now())
        TripAnalysis.objects.create(trip=trip, active_seconds=3600, distance_km=5.0, estimated_impressions=1000)
        CampaignInvoice.objects.create(campaign=self.campaign, invoice_number='INV-001', status='PAID', subtotal_price=100000, discount_amount=0, tax_amount=0, total_price=100000, expires_at=timezone.now()+timedelta(days=1), snapshot={})

        response = self.api.get('/v1/clients/reports/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_campaigns'], 1)
        self.assertEqual(response.data['total_hours_seen'], 1.0)
        self.assertEqual(response.data['total_cost'], 100000.0)
        self.assertEqual(response.data['total_days'], 5)  # active_days=5