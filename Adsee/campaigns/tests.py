from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from accounts.models import User
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType
from .models import (
    Campaign, CampaignSetting, CampaignDesign, CampaignArea,
    CampaignCost, CampaignCostItem, CampaignInvoice, Template
)
from print_shops.models import PrintShopProfile

class CampaignModelTest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(phone='09121110000', role=User.Role.CLIENT)
        self.client = ClientProfile.objects.create(user=self.client_user, full_name='Sara', national_id='1234567890')
        self.brand = Brand.objects.create(client=self.client, name='BrandX', slug='brandx')
        self.campaign = Campaign.objects.create(
            client=self.client,
            slogan='Test Slogan',
            brand_name=self.brand,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=10)
        )

    def test_campaign_is_active_now(self):
        self.assertEqual(self.campaign.status, Campaign.Status.DRAFT)
        self.assertFalse(self.campaign.is_active_now())
        self.campaign.status = Campaign.Status.ACTIVE
        self.campaign.save()
        self.assertTrue(self.campaign.is_active_now())

    def test_campaign_setting_creation(self):
        vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        setting = CampaignSetting.objects.create(
            campaign=self.campaign,
            active_days=5,
            activity_hours_per_day='08:00:00',
            max_driver=3,
            vehicle_type=vehicle_type
        )
        self.assertEqual(setting.max_driver, 3)

    def test_campaign_cost_items(self):
        cost = CampaignCost.objects.create(campaign=self.campaign)
        item = CampaignCostItem.objects.create(
            campaign_cost=cost,
            item_type=CampaignCostItem.ItemType.EXECUTION,
            title='Base execution',
            quantity=3,
            unit_price=10000
        )
        self.assertEqual(item.total_price, 30000)

    def test_invoice_snapshot(self):
        cost = CampaignCost.objects.create(campaign=self.campaign, total_price=150000)
        invoice = CampaignInvoice.objects.create(
            campaign=self.campaign,
            campaign_cost=cost,
            invoice_number='INV-001',
            status=CampaignInvoice.Status.ISSUED,
            subtotal_price=120000,
            discount_amount=0,
            tax_amount=30000,
            total_price=150000,
            expires_at=timezone.now() + timedelta(days=15),
            snapshot={'extra': 'data'}
        )
        self.assertEqual(invoice.snapshot['extra'], 'data')

    def test_design_print_assignment(self):
        print_user = User.objects.create_user(phone='09120009999', role=User.Role.PRINT_SHOP)
        shop = PrintShopProfile.objects.create(user=print_user, shop_name='چاپ سریع', address='...', phone='021')
        template = Template.objects.create(name='Test Template', variant='test-1')
        design = CampaignDesign.objects.create(
            campaign=self.campaign,
            design_type=CampaignDesign.DesignType.DEFAULT_TEMPLATE,
            print_shop=shop,
            print_status='ACCEPTED',
            template=template,
            estimated_ready_date=timezone.now() + timedelta(days=1)
        )
        self.assertEqual(design.print_shop, shop)
        self.assertEqual(design.print_status, 'ACCEPTED')