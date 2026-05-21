from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.gis.geos import Point

from accounts.models import User, ClientProfile, DriverProfile
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


class LongIntegrationTest(TestCase):
    def setUp(self):
        print("\n========== SETUP ==========")
        # ---------- Client & Brand ----------
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user, full_name='Client Sara', national_id='1234567890'
        )
        self.brand = Brand.objects.create(client=self.client_profile, name='MyBrand', slug='mybrand')
        print(f"✅ Client & Brand ready. Brand={self.brand.name}")

        # ---------- VehicleType ----------
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        print(f"✅ VehicleType ready. Rate={self.vehicle_type.base_hourly_rate}")

        # ---------- Campaign & Setting ----------
        self.campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='Long Test Campaign',
            brand_name=self.brand,
            start_date=date.today(),
            status=Campaign.Status.ACTIVE
        )
        self.campaign_setting = CampaignSetting.objects.create(
            campaign=self.campaign,
            active_days=5,
            activity_hours_per_day='08:00:00',
            max_driver=2,
            vehicle_type=self.vehicle_type
        )
        print(f"✅ Campaign ready. status={self.campaign.status}, end_date={self.campaign.end_date}")

        # ---------- Driver & Vehicle ----------
        self.driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user, full_name='Driver Ali', national_id='0987654321'
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver_profile,
            vehicle_type=self.vehicle_type,
            plate_number='12A345B67',
            banner_max_width_cm=100,
            banner_max_height_cm=50
        )
        print(f"✅ Driver & Vehicle ready. Plate={self.vehicle.plate_number}")

    # Mock کردن تابع‌های delay به‌گونه‌ای که خود تابع اصلی را صدا بزنند
    @patch('services.tasks.register_vehicle_task.delay', side_effect=register_vehicle_task)
    @patch('services.tasks.forward_location_to_analytics_task.delay', side_effect=forward_location_to_analytics_task)
    @patch('services.tasks.update_earnings_task.delay', side_effect=update_earnings_task)
    # Mock کردن متدهای کلاینت Analytics
    @patch.object(AnalyticsServiceClient, 'register_vehicle')
    @patch.object(AnalyticsServiceClient, 'send_single_location')
    @patch.object(AnalyticsServiceClient, 'calculate_earnings')
    def test_long_flow_with_earnings(
        self,
        mock_earnings, mock_send, mock_register,
        mock_update_delay, mock_forward_delay, mock_register_delay
    ):
        # شبیه‌سازی پاسخ‌های موفق
        mock_register.return_value = {"status": "ok"}
        mock_send.return_value = {"status": "ok"}
        mock_earnings.return_value = {"earnings": 150000.00}

        print("\n========== 1. CREATE TRIP ==========")
        trip = Trip.objects.create(
            driver=self.driver_profile,
            campaign=self.campaign,
            vehicle=self.vehicle,
            status=Trip.Status.PENDING
        )
        print(f"✅ Trip created (id={trip.id}, status={trip.status})")
        # حالا چون delay مستقیماً register_vehicle_task را صدا می‌زند، mock_register باید فعال شده باشد
        self.assertTrue(mock_register.called, "register_vehicle was not called")
        print("✅ register_vehicle called")

        print("\n========== 2. START TRIP ==========")
        trip.status = Trip.Status.ACTIVE
        trip.start_time = timezone.now() - timedelta(minutes=10)
        trip.save()
        print(f"✅ Trip started at {trip.start_time}")

        print("\n========== 3. SEND MULTIPLE LOCATIONS ==========")
        locations = [
            (51.39, 35.70),
            (51.40, 35.71),
            (51.41, 35.72),
            (51.42, 35.73),
            (51.43, 35.74),
        ]
        for i, (lon, lat) in enumerate(locations, 1):
            loc = DriverLocation.objects.create(
                driver=self.driver_user,
                trip=trip,
                point=Point(lon, lat, srid=4326)
            )
            print(f"   Location {i} sent (id={loc.id})")
        print(f"✅ {len(locations)} locations sent. send_single_location called {mock_send.call_count} times")
        self.assertEqual(mock_send.call_count, len(locations))

        print("\n========== 4. PAUSE AND RESUME ==========")
        trip.status = Trip.Status.PAUSED
        trip.save()
        print("✅ Trip paused")
        loc_paused = DriverLocation.objects.create(
            driver=self.driver_user,
            trip=trip,
            point=Point(51.44, 35.75, srid=4326)
        )
        # در حالت PAUSED، سیگنال موقعیت را ارسال نمی‌کند
        self.assertEqual(mock_send.call_count, len(locations))
        print("✅ Location during pause correctly not forwarded")

        trip.status = Trip.Status.ACTIVE
        trip.save()
        print("✅ Trip resumed")
        loc_after_resume = DriverLocation.objects.create(
            driver=self.driver_user,
            trip=trip,
            point=Point(51.45, 35.76, srid=4326)
        )
        self.assertEqual(mock_send.call_count, len(locations) + 1)
        print("✅ Location after resume forwarded")

        print("\n========== 5. COMPLETE TRIP AND FETCH EARNINGS ==========")
        trip.status = Trip.Status.COMPLETED
        trip.end_time = timezone.now()
        trip.save()
        print(f"✅ Trip completed at {trip.end_time}")

        # فراخوانی تسک درآمد (مستقیماً یا با delay که اکنون به تابع اصلی اشاره دارد)
        update_earnings_task.delay(trip.id)
        trip.refresh_from_db()

        print(f"   Earnings from mock: {trip.earnings}")
        self.assertEqual(trip.earnings, 150000.00)
        print("✅ Earnings correctly stored!")

        print("\n========== FINAL CHECK ==========")
        print(f"Trip status: {trip.status}, earnings: {trip.earnings} IRR")
        print("✅ ALL STEPS PASSED\n")