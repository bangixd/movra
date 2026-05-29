from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from decimal import Decimal

from accounts.models import User
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType
from campaigns.models import (
    Campaign, CampaignSetting, CampaignDesign, CampaignArea,
    CampaignInvoice, PaymentTransaction, CampaignGoal, BannerType
)
from geo.models import City
from django.contrib.gis.geos import Point, Polygon


class PaymentFlowTest(TestCase):
    def setUp(self):
        print("\n" + "="*60)
        print("   🚀 شروع تست جریان پرداخت کمپین")
        print("="*60)

        # ---------- کاربر کلاینت ----------
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user,
            full_name='Client Sara',
            national_id='1234567890'
        )
        print("✅ کلاینت ساخته شد")

        # ---------- برند ----------
        self.brand = Brand.objects.create(
            client=self.client_profile,
            name='Brand Test',
            slug='brand-test',
            phone='02112345678'
        )
        print("✅ برند ساخته شد")

        # ---------- نوع خودرو ----------
        self.vehicle_type = VehicleType.objects.create(
            name='Sedan',
            base_hourly_rate=Decimal('50000')
        )
        print("✅ نوع خودرو ساخته شد")

        # ---------- هدف کمپین و نوع بنر ----------
        self.goal = CampaignGoal.objects.create(name='افزایش فروش', is_active=True)
        self.banner_type = BannerType.objects.create(name='پوشش کامل بدنه', is_active=True)
        print("✅ هدف و نوع بنر ساخته شد")

        # ---------- کمپین ----------
        self.campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='کمپین تست',
            brand_name=self.brand,
            goal=self.goal,
            start_date=date.today(),
            status=Campaign.Status.DRAFT
        )
        print(f"✅ کمپین ساخته شد (id={self.campaign.id})")

        # ---------- تنظیمات (مرحله ۲) ----------
        self.setting = CampaignSetting.objects.create(
            campaign=self.campaign,
            active_days=5,
            activity_hours_per_day='08:00:00',
            max_driver=2,
            vehicle_type=self.vehicle_type
        )
        print("✅ تنظیمات کمپین ثبت شد")

        # ---------- طراحی (مرحله ۳) ----------
        self.design = CampaignDesign.objects.create(
            campaign=self.campaign,
            design_type=CampaignDesign.DesignType.USER_UPLOAD,
            banner_type=self.banner_type,
            status=CampaignDesign.DesignStatus.PENDING
        )
        print("✅ طراحی کمپین ثبت شد")

        # ---------- محدوده (مرحله ۴) ----------
        self.city = City.objects.create(
            name='تهران',
            center=Point(51.38, 35.68, srid=4326)
        )
        poly = Polygon(((51.0, 35.0), (51.0, 36.0), (52.0, 36.0), (52.0, 35.0), (51.0, 35.0)), srid=4326)
        self.area = CampaignArea.objects.create(
            campaign=self.campaign,
            area_type=CampaignArea.AreaType.FREE_AREA,
            city=self.city,
            region_polygon=poly
        )
        print("✅ محدودهٔ کمپین ثبت شد")

        # ---------- API Client ----------
        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)
        print("✅ احراز هویت انجام شد")
        print("-"*60)

    # ==============================
    # تست ۱: محاسبهٔ هزینه
    # ==============================
    def test_01_calculate_cost(self):
        print("\n📊 تست ۱: محاسبهٔ هزینه")
        response = self.api.get(f'/api/campaigns/{self.campaign.id}/cost/')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.data}")

        self.assertEqual(response.status_code, 200)
        self.assertIn('total', response.data)
        self.assertIn('design', response.data)
        self.assertIn('area', response.data)
        self.assertIn('vehicle', response.data)
        self.assertGreater(response.data['total'], 0)
        print("✅ محاسبهٔ هزینه با موفقیت انجام شد")

    # ==============================
    # تست ۲: درخواست پرداخت (ساخت فاکتور و تراکنش)
    # ==============================
    @patch('services.payment_gateway.ZarinpalGateway.send_request')
    def test_02_request_payment(self, mock_send):
        print("\n💳 تست ۲: درخواست پرداخت")

        # شبیه‌سازی پاسخ موفق زرین‌پال
        mock_send.return_value = (True, 'https://sandbox.zarinpal.com/pg/StartPay/ABC123', None)

        response = self.api.post('/api/campaigns/payments/request/', {
            'campaign_id': self.campaign.id
        }, format='json')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.data}")

        self.assertEqual(response.status_code, 200)
        self.assertIn('payment_url', response.data)
        self.assertIn('invoice_id', response.data)

        # بررسی ذخیره‌سازی در دیتابیس
        invoice = CampaignInvoice.objects.get(campaign=self.campaign)
        self.assertEqual(invoice.status, CampaignInvoice.Status.ISSUED)
        self.assertIsNotNone(invoice.expires_at)
        self.assertGreater(invoice.total_price, 0)

        transaction = PaymentTransaction.objects.get(invoice=invoice)
        self.assertEqual(transaction.status, PaymentTransaction.Status.INITIATED)
        self.assertEqual(transaction.authority, 'ABC123')

        print(f"   شماره فاکتور: {invoice.invoice_number}")
        print(f"   مبلغ: {invoice.total_price} تومان")
        print(f"   تاریخ انقضا: {invoice.expires_at}")
        print("✅ درخواست پرداخت با موفقیت ثبت شد")

    # ==============================
    # تست ۳: تأیید پرداخت موفق
    # ==============================
    @patch('services.payment_gateway.ZarinpalGateway.verify_payment')
    def test_03_verify_successful(self, mock_verify):
        print("\n✅ تست ۳: تأیید پرداخت موفق")

        # ابتدا یک فاکتور و تراکنش ایجاد کن
        invoice = CampaignInvoice.objects.create(
            campaign=self.campaign,
            invoice_number='INV-TEST-001',
            status=CampaignInvoice.Status.ISSUED,
            subtotal_price=500000,
            discount_amount=0,
            tax_amount=45000,
            total_price=545000,
            expires_at=timezone.now() + timedelta(minutes=15),
            snapshot={'test': 'data'}
        )
        transaction = PaymentTransaction.objects.create(
            invoice=invoice,
            authority='ABC123',
            amount=545000,
            status=PaymentTransaction.Status.INITIATED
        )
        print(f"   فاکتور تستی ساخته شد (شماره: {invoice.invoice_number})")

        # شبیه‌سازی پاسخ تأیید زرین‌پال
        mock_verify.return_value = (True, 'REF123456')

        response = self.api.get('/api/campaigns/payments/verify/?Authority=ABC123&Status=OK')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.data}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')

        # بررسی بروزرسانی‌ها
        invoice.refresh_from_db()
        transaction.refresh_from_db()
        self.campaign.refresh_from_db()

        self.assertEqual(invoice.status, CampaignInvoice.Status.PAID)
        self.assertIsNotNone(invoice.paid_at)
        self.assertEqual(transaction.status, PaymentTransaction.Status.SUCCESSFUL)
        self.assertEqual(transaction.ref_id, 'REF123456')
        self.assertEqual(self.campaign.status, Campaign.Status.ACTIVE)

        print(f"   وضعیت فاکتور: {invoice.status}")
        print(f"   وضعیت کمپین: {self.campaign.status}")
        print(f"   شماره پیگیری: {transaction.ref_id}")
        print("✅ پرداخت با موفقیت تأیید شد و کمپین فعال گردید")

    # ==============================
    # تست ۴: تأیید پرداخت ناموفق
    # ==============================
    @patch('services.payment_gateway.ZarinpalGateway.verify_payment')
    def test_04_verify_failed(self, mock_verify):
        print("\n❌ تست ۴: تأیید پرداخت ناموفق")

        # ساخت فاکتور و تراکنش تستی
        invoice = CampaignInvoice.objects.create(
            campaign=self.campaign,
            invoice_number='INV-TEST-002',
            status=CampaignInvoice.Status.ISSUED,
            subtotal_price=500000,
            discount_amount=0,
            tax_amount=45000,
            total_price=545000,
            expires_at=timezone.now() + timedelta(minutes=15),
            snapshot={}
        )
        transaction = PaymentTransaction.objects.create(
            invoice=invoice,
            authority='FAIL123',
            amount=545000,
            status=PaymentTransaction.Status.INITIATED
        )

        # شبیه‌سازی پاسخ ناموفق
        mock_verify.return_value = (False, 101)  # کد خطای زرین‌پال

        response = self.api.get('/api/campaigns/payments/verify/?Authority=FAIL123&Status=OK')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.data}")

        self.assertEqual(response.status_code, 400)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, PaymentTransaction.Status.FAILED)

        print(f"   وضعیت تراکنش: {transaction.status}")
        print("✅ پرداخت ناموفق به‌درستی ثبت شد")

    # ==============================
    # تست ۵: لغو پرداخت توسط کاربر
    # ==============================
    def test_05_user_cancelled(self):
        print("\n🚫 تست ۵: لغو پرداخت توسط کاربر")

        invoice = CampaignInvoice.objects.create(
            campaign=self.campaign,
            invoice_number='INV-TEST-003',
            status=CampaignInvoice.Status.ISSUED,
            subtotal_price=500000,
            discount_amount=0,
            tax_amount=45000,
            total_price=545000,
            expires_at=timezone.now() + timedelta(minutes=15),
            snapshot={}
        )
        transaction = PaymentTransaction.objects.create(
            invoice=invoice,
            authority='CANCEL123',
            amount=545000,
            status=PaymentTransaction.Status.INITIATED
        )

        response = self.api.get('/api/campaigns/payments/verify/?Authority=CANCEL123&Status=NOK')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.data}")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['status'], 'cancelled')
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, PaymentTransaction.Status.FAILED)

        print(f"   وضعیت تراکنش: {transaction.status}")
        print("✅ لغو پرداخت به‌درستی مدیریت شد")

    # ==============================
    # تست ۶: انقضای فاکتور
    # ==============================
    def test_06_invoice_expiry(self):
        print("\n⏰ تست ۶: انقضای فاکتور")

        # ساخت فاکتور منقضی
        invoice = CampaignInvoice.objects.create(
            campaign=self.campaign,
            invoice_number='INV-TEST-004',
            status=CampaignInvoice.Status.ISSUED,
            subtotal_price=500000,
            discount_amount=0,
            tax_amount=45000,
            total_price=545000,
            expires_at=timezone.now() - timedelta(minutes=1),  # گذشته
            snapshot={}
        )

        # تلاش برای پرداخت با فاکتور منقضی
        response = self.api.post('/api/campaigns/payments/request/', {
            'campaign_id': self.campaign.id
        }, format='json')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.data}")

        # باید خطا برگرداند چون فاکتور ISSUED قبلی منقضی شده
        self.assertEqual(response.status_code, 400)
        self.assertIn('منقضی', response.data.get('error', ''))

        # حالا تسک انقضا را اجرا کن
        from services.tasks import expire_pending_invoices
        expire_pending_invoices()

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, CampaignInvoice.Status.EXPIRED)
        print(f"   وضعیت فاکتور پس از تسک: {invoice.status}")
        print("✅ انقضای فاکتور به‌درستی کار می‌کند")

    # ==============================
    # تست ۷: پرداخت مجدد (ساخت فاکتور جدید)
    # ==============================
    @patch('services.payment_gateway.ZarinpalGateway.send_request')
    def test_07_retry_payment_after_expiry(self, mock_send):
        print("\n🔄 تست ۷: پرداخت مجدد پس از انقضا")

        # یک فاکتور منقضی بساز
        CampaignInvoice.objects.create(
            campaign=self.campaign,
            invoice_number='INV-TEST-005',
            status=CampaignInvoice.Status.EXPIRED,
            subtotal_price=500000,
            discount_amount=0,
            tax_amount=45000,
            total_price=545000,
            expires_at=timezone.now() - timedelta(minutes=10),
            snapshot={}
        )

        # حالا دوباره درخواست پرداخت بده
        mock_send.return_value = (True, 'https://sandbox.zarinpal.com/pg/StartPay/NEW456', None)
        response = self.api.post('/api/campaigns/payments/request/', {
            'campaign_id': self.campaign.id
        }, format='json')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.data}")

        self.assertEqual(response.status_code, 200)

        # باید یک فاکتور ISSUED جدید ساخته شده باشد
        new_invoice = CampaignInvoice.objects.filter(
            campaign=self.campaign,
            status=CampaignInvoice.Status.ISSUED
        ).first()
        self.assertIsNotNone(new_invoice)
        self.assertNotEqual(new_invoice.invoice_number, 'INV-TEST-005')
        print(f"   شماره فاکتور جدید: {new_invoice.invoice_number}")
        print("✅ فاکتور جدید با موفقیت ساخته شد و امکان پرداخت مجدد فراهم است")

    def tearDown(self):
        print("\n" + "="*60)
        print("   🏁 پایان تست جریان پرداخت")
        print("="*60 + "\n")