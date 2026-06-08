from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from accounts.models import User
from drivers.models import DriverProfile
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType
from campaigns.models import Campaign, CampaignSetting, CampaignDesign, CampaignArea, CampaignInvoice, PaymentTransaction
from campaigns.services.campaign_service import CampaignService
from geo.models import City, Province
from django.contrib.gis.geos import Polygon, Point


class CampaignServiceTest(TestCase):
    def setUp(self):
        print("\n========== CampaignService Test Setup ==========")
        # Client
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user, full_name='Test Client', national_id='1234567890'
        )
        self.brand = Brand.objects.create(client=self.client_profile, name='Test Brand', slug='test-brand')

        # VehicleType
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)

        # Campaign
        self.campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='Test Campaign',
            brand_name=self.brand,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=10),
            status=Campaign.Status.DRAFT
        )
        self.setting = CampaignSetting.objects.create(
            campaign=self.campaign,
            active_days=5,
            activity_hours_per_day='08:00:00',
            max_driver=2,
            vehicle_type=self.vehicle_type
        )
        # City & Area
        self.city = City.objects.create(name='Tehran', province=None, center=Point(51.38, 35.68, srid=4326))
        poly = Polygon(((51.0, 35.0), (51.0, 36.0), (52.0, 36.0), (52.0, 35.0), (51.0, 35.0)), srid=4326)
        self.area = CampaignArea.objects.create(
            campaign=self.campaign, area_type='FREE_AREA', city=self.city, region_polygon=poly
        )
        # Design
        self.design = CampaignDesign.objects.create(
            campaign=self.campaign,
            design_type=CampaignDesign.DesignType.USER_UPLOAD,
            status=CampaignDesign.DesignStatus.COMPLETED
        )
        print("✅ Setup complete")

    # ========== get_queryset ==========
    def test_get_queryset_admin(self):
        print("\n--- TEST: get_queryset - Admin ---")
        admin = User.objects.create_superuser(phone='09990000000', password='admin')
        qs = CampaignService.get_queryset(admin)
        self.assertEqual(qs.count(), 1)
        print("✅ Admin sees all campaigns")

    def test_get_queryset_client_own(self):
        print("\n--- TEST: get_queryset - Client (own) ---")
        qs = CampaignService.get_queryset(self.client_user)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), self.campaign)
        print("✅ Client sees own campaign")

    def test_get_queryset_client_other(self):
        print("\n--- TEST: get_queryset - Client (other) ---")
        other_user = User.objects.create_user(phone='09220000000', role=User.Role.CLIENT)
        other_profile = ClientProfile.objects.create(user=other_user, full_name='Other', national_id='9999999999')
        qs = CampaignService.get_queryset(other_user)
        self.assertEqual(qs.count(), 0)
        print("✅ Client does NOT see other's campaign")

    # ========== toggle_pause ==========
    def test_toggle_pause_active_to_paused(self):
        print("\n--- TEST: toggle_pause - ACTIVE → PAUSED ---")
        self.campaign.status = Campaign.Status.ACTIVE
        self.campaign.save()
        result = CampaignService.toggle_pause(self.campaign)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, Campaign.Status.PAUSED)
        self.assertEqual(result['status'], 'PAUSED')
        print("✅ Campaign paused")

    def test_toggle_pause_paused_to_active(self):
        print("\n--- TEST: toggle_pause - PAUSED → ACTIVE ---")
        self.campaign.status = Campaign.Status.PAUSED
        self.campaign.save()
        result = CampaignService.toggle_pause(self.campaign)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, Campaign.Status.ACTIVE)
        print("✅ Campaign resumed")

    def test_toggle_pause_invalid_status(self):
        print("\n--- TEST: toggle_pause - Invalid Status ---")
        self.campaign.status = Campaign.Status.COMPLETED
        self.campaign.save()
        with self.assertRaises(ValueError):
            CampaignService.toggle_pause(self.campaign)
        print("✅ ValueError raised")

    # ========== add_vehicles (mocked) ==========
    @patch('campaigns.services.campaign_service.ZarinpalGateway.send_request')
    def test_add_vehicles_success(self, mock_send):
        print("\n--- TEST: add_vehicles - Success ---")
        mock_send.return_value = (True, 'https://sandbox.zarinpal.com/pg/StartPay/ABC123', None)
        self.campaign.status = Campaign.Status.ACTIVE
        self.campaign.save()

        result = CampaignService.add_vehicles(self.campaign, 3)
        self.assertIn('payment_url', result)
        self.assertIn('invoice_id', result)
        self.assertEqual(PaymentTransaction.objects.count(), 1)
        invoice = CampaignInvoice.objects.last()
        self.assertEqual(invoice.modification_type, 'ADD_VEHICLES')
        self.assertEqual(invoice.modification_data['additional_vehicles'], 3)
        print("✅ Add vehicles invoice created & payment initiated")

    @patch('campaigns.services.campaign_service.ZarinpalGateway.send_request')
    def test_add_vehicles_gateway_failure(self, mock_send):
        print("\n--- TEST: add_vehicles - Gateway Failure ---")
        mock_send.return_value = (False, None, 'Gateway error')
        self.campaign.status = Campaign.Status.ACTIVE
        self.campaign.save()

        with self.assertRaises(ConnectionError):
            CampaignService.add_vehicles(self.campaign, 2)
        # فاکتور باید void شده باشد
        invoice = CampaignInvoice.objects.last()
        self.assertEqual(invoice.status, CampaignInvoice.Status.VOID)
        print("✅ Invoice voided on gateway failure")

    def test_add_vehicles_invalid_status(self):
        print("\n--- TEST: add_vehicles - Invalid Status ---")
        self.campaign.status = Campaign.Status.COMPLETED
        self.campaign.save()
        with self.assertRaises(ValueError):
            CampaignService.add_vehicles(self.campaign, 2)
        print("✅ ValueError raised")