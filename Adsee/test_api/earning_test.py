from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.gis.geos import Point

from accounts.models import User
from drivers.models import DriverProfile
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting
from geo.models import DriverLocation
from trips.models import Trip
from services.analytics_client import AnalyticsServiceClient
from services.tasks import (
    register_vehicle_task,
    forward_location_to_analytics_task,
    update_earnings_task,
)

class EarningsTest(TestCase):
    def setUp(self):
        print("\n========== SETUP ==========")
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
        self.driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(user=self.driver_user, first_name='D', last_name='D', national_id='0987654321')
        self.vehicle = Vehicle.objects.create(
            driver=self.driver_profile, vehicle_type=self.vehicle_type,
            plate_number='12A345B67', banner_max_width_cm=100, banner_max_height_cm=50
        )
        print("✅ Setup complete")

    @patch.object(AnalyticsServiceClient, 'calculate_earnings')
    @patch.object(AnalyticsServiceClient, 'send_single_location')
    @patch.object(AnalyticsServiceClient, 'register_vehicle')
    def test_earnings_filled(self, mock_register, mock_send, mock_earnings):
        # پیکربندی Mockها
        mock_register.return_value = {"status": "ok"}
        mock_send.return_value = {"status": "ok"}
        mock_earnings.return_value = {"earnings": 150000.00}
        print("✅ Mocks configured")

        print("\n========== 1. CREATE TRIP ==========")
        trip = Trip.objects.create(driver=self.driver_profile, campaign=self.campaign, vehicle=self.vehicle)
        print(f"✅ Trip created (id={trip.id}, status={trip.status})")

        print("   Calling register_vehicle_task directly...")
        register_vehicle_task(
            vehicle_plate=self.vehicle.plate_number,
            display_name=f"{self.vehicle.plate_number} - {self.driver_profile.full_name}",
            driver_id=self.driver_profile.id,
            driver_name=self.driver_profile.full_name,
            driver_phone=self.driver_user.phone,
            created_at=trip.created_at,
            updated_at=trip.updated_at,
        )
        self.assertTrue(mock_register.called, "register_vehicle was not called")
        print("✅ register_vehicle called")

        print("\n========== 2. START TRIP ==========")
        trip.status = Trip.Status.ACTIVE
        trip.start_time = timezone.now() - timedelta(minutes=10)
        trip.save()
        print(f"✅ Trip started at {trip.start_time}")

        print("\n========== 3. SEND LOCATION ==========")
        loc = DriverLocation.objects.create(
            driver=self.driver_user, trip=trip,
            point=Point(51.39, 35.70, srid=4326)
        )
        print(f"✅ Location created (id={loc.id})")
        print("   Calling forward_location_to_analytics_task directly...")
        forward_location_to_analytics_task(
            driver_id=self.driver_user.id,
            trip_id=trip.id,
            vehicle_plate=self.vehicle.plate_number,
            campaign_id=self.campaign.id,
            lat=loc.point.y,
            lon=loc.point.x,
            speed=0,
            heading=0,
            timestamp=int(loc.timestamp.timestamp()),
        )
        self.assertTrue(mock_send.called, "send_single_location was not called")
        print("✅ send_single_location called")

        print("\n========== 4. COMPLETE TRIP ==========")
        trip.status = Trip.Status.COMPLETED
        trip.end_time = timezone.now()
        trip.save()
        print(f"✅ Trip completed at {trip.end_time}")

        print("\n========== 5. FETCH EARNINGS ==========")
        print("   Calling update_earnings_task directly...")
        update_earnings_task(trip.id)
        self.assertTrue(mock_earnings.called, "calculate_earnings was not called")
        print("✅ calculate_earnings called")

        trip.refresh_from_db()
        print(f"   Earnings: {trip.earnings} Toman")
        self.assertEqual(trip.earnings, 150000.00)
        print("✅ Earnings correctly stored!")

        print("\n========== FINAL STATUS ==========")
        print(f"Trip status: {trip.status}")
        print(f"Trip earnings: {trip.earnings} IRR")
        print("✅ ALL CHECKS PASSED\n")