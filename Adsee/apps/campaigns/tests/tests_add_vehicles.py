from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from datetime import date, timedelta
from accounts.models import User
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType
from django.contrib.gis.geos import Point, Polygon
from geo.models import City
from campaigns.models import (
    Campaign, CampaignSetting, CampaignInvoice, PaymentTransaction, BannerType, CampaignDesign, CampaignArea
)


class AddVehiclesTest(TestCase):
    def setUp(self):
        # کاربر کلاینت
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user, full_name='Client Sara', national_id='1234567890'
        )
        # اضافه کردن محدوده (area)
        city = City.objects.create(name='Test City', center=Point(51.38, 35.68, srid=4326))
        polygon = Polygon(((51.0, 35.0), (51.0, 36.0), (52.0, 36.0), (52.0, 35.0), (51.0, 35.0)), srid=4326)
        self.brand = Brand.objects.create(client=self.client_profile, name='Brand', slug='b')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='کمپین تست',
            brand_name=self.brand,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
            status=Campaign.Status.ACTIVE
        )
        self.design = CampaignDesign.objects.create(
            campaign=self.campaign,
            design_type=CampaignDesign.DesignType.USER_UPLOAD,  # یا هر نوع معتبر
            status=CampaignDesign.DesignStatus.COMPLETED
        )
        self.area = CampaignArea.objects.create(
            campaign=self.campaign,
            area_type=CampaignArea.AreaType.FREE_AREA,
            city=city,
            region_polygon=polygon
        )
        CampaignSetting.objects.create(
            campaign=self.campaign,
            active_days=5,
            activity_hours_per_day='08:00:00',
            max_driver=2,
            vehicle_type=self.vehicle_type
        )
        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)

    @patch('services.payment_gateway.ZarinpalGateway.send_request')
    def test_add_vehicles(self, mock_send):
        # شبیه‌سازی پاسخ موفق زرین‌پال
        mock_send.return_value = (True, 'https://sandbox.zarinpal.com/pg/StartPay/ADD123', None)

        response = self.api.post(f'/v1/campaigns/{self.campaign.id}/add-vehicles/', {
            'count': 3
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('payment_url', response.data)
        self.assertIn('invoice_id', response.data)

        # بررسی فاکتور
        invoice = CampaignInvoice.objects.get(modification_type='ADD_VEHICLES')
        self.assertEqual(invoice.modification_data['additional_vehicles'], 3)
        self.assertEqual(invoice.modification_data['new_max_driver'], 5)  # قبلاً 2 بوده، 3 اضافه = 5
        self.assertGreater(invoice.total_price, 0)

        # بررسی تراکنش
        transaction = PaymentTransaction.objects.get(invoice=invoice)
        self.assertEqual(transaction.amount, invoice.total_price)
        self.assertEqual(transaction.status, PaymentTransaction.Status.INITIATED)
        self.assertEqual(transaction.authority, 'ADD123')