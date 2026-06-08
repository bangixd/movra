from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from accounts.models import User
from drivers.models import DriverProfile
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting, CampaignDesign, CampaignArea
from trips.models import Trip, TripAnalysis
from campaigns.services.campaign_report_service import CampaignReportService
from geo.models import City
from django.contrib.gis.geos import Polygon, Point


class CampaignReportServiceTest(TestCase):
    def setUp(self):
        print("\n========== CampaignReportService Test Setup ==========")
        # Client & Campaign
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='TC', national_id='1234567890')
        self.brand = Brand.objects.create(client=self.client_profile, name='Test Brand', slug='test-brand')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.campaign = Campaign.objects.create(
            client=self.client_profile, slogan='Test', brand_name=self.brand,
            start_date=date.today(), end_date=date.today() + timedelta(days=5),
            status=Campaign.Status.ACTIVE
        )
        self.setting = CampaignSetting.objects.create(
            campaign=self.campaign, active_days=5, activity_hours_per_day='08:00:00',
            max_driver=2, vehicle_type=self.vehicle_type
        )
        city = City.objects.create(name='Tehran', province=None, center=Point(51.38, 35.68, srid=4326))
        poly = Polygon(((51.0, 35.0), (51.0, 36.0), (52.0, 36.0), (52.0, 35.0), (51.0, 35.0)), srid=4326)
        CampaignArea.objects.create(campaign=self.campaign, area_type='FREE_AREA', city=city, region_polygon=poly)
        CampaignDesign.objects.create(campaign=self.campaign, design_type='USER_UPLOAD', status='COMPLETED')

        # Driver & Trip
        self.driver_user = User.objects.create_user(phone='09221112233', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(user=self.driver_user, full_name='Test Driver', national_id='9999999999')
        self.vehicle = Vehicle.objects.create(
            driver=self.driver_profile, vehicle_type=self.vehicle_type,
            plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50
        )
        self.trip = Trip.objects.create(
            driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
            status=Trip.Status.COMPLETED,
            start_time=timezone.now() - timedelta(hours=2),
            end_time=timezone.now(),
            earnings=125000.00
        )
        self.analysis = TripAnalysis.objects.create(
            trip=self.trip, active_seconds=3600, distance_km=15.0,
            exposure_score=0.75, estimated_impressions=1200,
            data_quality=0.95, confidence=0.9, avg_traffic_ratio=1.1
        )
        print("✅ Setup complete")

    # ========== check_access ==========
    def test_check_access_owner(self):
        print("\n--- TEST: check_access - Owner ---")
        try:
            CampaignReportService.check_access(self.client_user, self.campaign)
        except PermissionError:
            self.fail("Owner should have access")
        print("✅ Owner has access")

    def test_check_access_other_client(self):
        print("\n--- TEST: check_access - Other Client ---")
        other_user = User.objects.create_user(phone='09330000000', role=User.Role.CLIENT)
        ClientProfile.objects.create(user=other_user, full_name='Other', national_id='8888888888')
        with self.assertRaises(PermissionError):
            CampaignReportService.check_access(other_user, self.campaign)
        print("✅ PermissionError raised")

    def test_check_access_admin(self):
        print("\n--- TEST: check_access - Admin ---")
        admin = User.objects.create_superuser(phone='09990000000', password='admin')
        try:
            CampaignReportService.check_access(admin, self.campaign)
        except PermissionError:
            self.fail("Admin should have access")
        print("✅ Admin has access")

    # ========== get_trip_analyses_for_campaign ==========
    def test_get_trip_analyses_for_campaign(self):
        print("\n--- TEST: get_trip_analyses_for_campaign ---")
        analyses = CampaignReportService.get_trip_analyses_for_campaign(self.campaign.id, self.client_user)
        self.assertEqual(analyses.count(), 1)
        self.assertEqual(analyses.first(), self.analysis)
        print("✅ Analyses returned correctly")

    # ========== get_completed_trip_analyses ==========
    def test_get_completed_trip_analyses(self):
        print("\n--- TEST: get_completed_trip_analyses ---")
        analyses = CampaignReportService.get_completed_trip_analyses(self.campaign)
        self.assertEqual(analyses.count(), 1)
        print("✅ Completed analyses returned")

    # ========== generate_csv_response ==========
    def test_generate_csv_response(self):
        print("\n--- TEST: generate_csv_response ---")
        analyses = CampaignReportService.get_completed_trip_analyses(self.campaign)
        response = CampaignReportService.generate_csv_response(self.campaign, analyses)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8-sig')
        self.assertIn('شناسه سفر', content)
        self.assertIn('Test Driver', content)
        self.assertIn('125000.00', content)
        print("✅ CSV generated with correct headers & data")