from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from accounts.models import User
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType
from campaigns.models import Campaign, CampaignSetting, CampaignDesign, CampaignArea, CampaignInvoice
from campaigns.services.invoice_service import InvoiceService
from geo.models import City
from django.contrib.gis.geos import Polygon, Point


class InvoiceServiceTest(TestCase):
    def setUp(self):
        print("\n========== InvoiceService Test Setup ==========")
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user, full_name='Test Client', national_id='1234567890'
        )
        self.brand = Brand.objects.create(client=self.client_profile, name='Test Brand', slug='test-brand')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
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
        city = City.objects.create(name='Tehran', province=None, center=Point(51.38, 35.68, srid=4326))
        poly = Polygon(((51.0, 35.0), (51.0, 36.0), (52.0, 36.0), (52.0, 35.0), (51.0, 35.0)), srid=4326)
        self.area = CampaignArea.objects.create(campaign=self.campaign, area_type='FREE_AREA', city=city, region_polygon=poly)
        self.design = CampaignDesign.objects.create(
            campaign=self.campaign,
            design_type=CampaignDesign.DesignType.USER_UPLOAD,
            status=CampaignDesign.DesignStatus.COMPLETED
        )
        print("✅ Setup complete")

    # ========== create_modification_invoice ==========
    def test_create_modification_invoice(self):
        print("\n--- TEST: create_modification_invoice ---")
        extra_amount = Decimal('100000')
        invoice = InvoiceService.create_modification_invoice(
            campaign=self.campaign,
            modification_type='ADD_VEHICLES',
            extra_amount=extra_amount,
            modification_data={'test': 'data'},
        )
        self.assertEqual(invoice.subtotal_price, extra_amount)
        self.assertEqual(invoice.tax_amount, extra_amount * Decimal('0.09'))
        self.assertEqual(invoice.total_price, extra_amount * Decimal('1.09'))
        self.assertEqual(invoice.status, CampaignInvoice.Status.ISSUED)
        self.assertIsNotNone(invoice.expires_at)
        self.assertEqual(invoice.modification_type, 'ADD_VEHICLES')
        print("✅ Invoice created with correct amounts & type")

    # ========== mark_as_paid ==========
    def test_mark_as_paid_success(self):
        print("\n--- TEST: mark_as_paid - Success ---")
        invoice = CampaignInvoice.objects.create(
            campaign=self.campaign,
            invoice_number='INV-001',
            subtotal_price=100000,
            discount_amount=0,
            tax_amount=9000,
            total_price=109000,
            expires_at=timezone.now() + timedelta(minutes=15),
            status=CampaignInvoice.Status.ISSUED,
        )
        updated = InvoiceService.mark_as_paid(invoice)
        self.assertEqual(updated.status, CampaignInvoice.Status.PAID)
        self.assertIsNotNone(updated.paid_at)
        print("✅ Invoice marked as paid")

    def test_mark_as_paid_invalid_status(self):
        print("\n--- TEST: mark_as_paid - Invalid Status ---")
        invoice = CampaignInvoice.objects.create(
            campaign=self.campaign,
            invoice_number='INV-002',
            subtotal_price=100000,
            discount_amount=0,
            tax_amount=9000,
            total_price=109000,
            expires_at=timezone.now() + timedelta(minutes=15),
            status=CampaignInvoice.Status.PAID,  # قبلاً پرداخت شده
        )
        with self.assertRaises(ValueError):
            InvoiceService.mark_as_paid(invoice)
        print("✅ ValueError raised for already paid invoice")

    # ========== get_queryset ==========
    def test_get_queryset_client(self):
        print("\n--- TEST: get_queryset - Client ---")
        invoice = CampaignInvoice.objects.create(
            campaign=self.campaign,
            invoice_number='INV-003',
            subtotal_price=50000, discount_amount=0, tax_amount=4500, total_price=54500,
            expires_at=timezone.now() + timedelta(minutes=15),
            status=CampaignInvoice.Status.ISSUED,
        )
        qs = InvoiceService.get_queryset(self.client_user)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), invoice)
        print("✅ Client sees own invoice")

    def test_get_queryset_admin(self):
        print("\n--- TEST: get_queryset - Admin ---")
        invoice = CampaignInvoice.objects.create(
            campaign=self.campaign,
            invoice_number='INV-004',
            subtotal_price=50000, discount_amount=0, tax_amount=4500, total_price=54500,
            expires_at=timezone.now() + timedelta(minutes=15),
            status=CampaignInvoice.Status.ISSUED,
        )
        admin = User.objects.create_superuser(phone='09990000000', password='admin')
        qs = InvoiceService.get_queryset(admin)
        self.assertEqual(qs.count(), 1)
        print("✅ Admin sees all invoices")