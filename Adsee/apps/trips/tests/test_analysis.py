from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import patch
from django.contrib.gis.geos import Point

from accounts.models import User
from clients.models import ClientProfile
from drivers.models import DriverProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting
from geo.models import DriverLocation
from trips.models import Trip, TripAnalysis
from services.analytics_client import AnalyticsServiceClient

class TripAnalysisAPITest(TestCase):
    def setUp(self):
        print("\n========== SETUP ==========")
        # کلاینت و کمپین
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='C', national_id='1234567890')
        self.brand = Brand.objects.create(client=self.client_profile, name='B', slug='b')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.campaign = Campaign.objects.create(
            client=self.client_profile, slogan='Test', brand_name=self.brand,
            start_date=date.today(), status=Campaign.Status.ACTIVE
        )
        self.campaign_setting = CampaignSetting.objects.create(
            campaign=self.campaign, active_days=5, activity_hours_per_day='08:00:00', max_driver=2, vehicle_type=self.vehicle_type
        )
        # راننده و خودرو
        self.driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(user=self.driver_user, full_name='D', national_id='0987654321')
        self.vehicle = Vehicle.objects.create(
            driver=self.driver_profile, vehicle_type=self.vehicle_type,
            plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50
        )
        # سفر
        self.trip = Trip.objects.create(
            driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle,
            status=Trip.Status.ACTIVE, start_time=timezone.now() - timedelta(minutes=10)
        )
        self.trip.end_time = timezone.now()
        self.trip.status = Trip.Status.COMPLETED
        self.trip.save()

        self.api = APIClient()
        self.api.force_authenticate(user=self.driver_user)

    @patch.object(AnalyticsServiceClient, 'get_analysis_summary')
    @patch.object(AnalyticsServiceClient, 'create_analysis_run')
    def test_fetch_and_store_analysis(self, mock_run, mock_summary):
        mock_summary.return_value = {
            'active_seconds': 600, 'distance_km': 5.0, 'exposure_score': 0.85,
            'estimated_impressions': 1200, 'data_quality': 0.95, 'confidence': 0.9,
            'avg_traffic_ratio': 1.2
        }
        mock_run.return_value = {'run_id': 'run-123'}

        from services.tasks import fetch_and_store_trip_analysis
        fetch_and_store_trip_analysis(self.trip.id)

        analysis = TripAnalysis.objects.get(trip=self.trip)
        self.assertEqual(analysis.active_seconds, 600)
        self.assertEqual(analysis.analysis_run_id, 'run-123')

    @patch.object(AnalyticsServiceClient, 'get_analysis_summary')
    def test_analysis_api(self, mock_summary):
        # ذخیره یک تحلیل دستی
        TripAnalysis.objects.create(
            trip=self.trip, active_seconds=500, distance_km=3.0,
            exposure_score=0.7, estimated_impressions=800,
            analysis_run_id='run-abc'
        )
        response = self.api.get(f'/v1/trips/{self.trip.id}/analysis/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['active_seconds'], 500)

    def test_analysis_not_found(self):
        response = self.api.get(f'/v1/trips/{self.trip.id}/analysis/')
        self.assertEqual(response.status_code, 404)

    @patch('services.tasks.fetch_and_store_trip_analysis.delay')
    def test_refresh_analysis(self, mock_delay):
        response = self.api.post(f'/v1/trips/{self.trip.id}/refresh_analysis/')
        self.assertEqual(response.status_code, 202)
        mock_delay.assert_called_with(self.trip.id)

    def test_export_csv(self):
        # یک تحلیل اضافه کن
        TripAnalysis.objects.create(trip=self.trip, active_seconds=500, distance_km=3.0,
                                    exposure_score=0.7, estimated_impressions=800)
        response = self.api.get('/v1/trips/export_csv/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('trip_id', content)
        self.assertIn('500', content)  # active_seconds در CSV