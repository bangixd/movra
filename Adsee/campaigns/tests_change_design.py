# campaigns/tests_change_design.py
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from accounts.models import User, ClientProfile
from brands.models import Brand
from campaigns.models import (
    Campaign, CampaignSetting, CampaignDesign, CampaignInvoice,
    BannerType, CampaignPricingRule
)

class ChangeDesignTest(TestCase):
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
        self.banner_type = BannerType.objects.create(name='استیکر روی درها', is_active=True)
        self.design = CampaignDesign.objects.create(
            campaign=self.campaign,
            design_type='USER_UPLOAD',
            banner_type=self.banner_type,
            status=CampaignDesign.DesignStatus.COMPLETED
        )
        # نرخ‌ها
        CampaignPricingRule.objects.create(key='DESIGN_BASE_COST', value_type='DECIMAL', decimal_value=50000, is_active=True)
        CampaignPricingRule.objects.create(key='DESIGN_CUSTOM_COST', value_type='DECIMAL', decimal_value=200000, is_active=True)
        CampaignPricingRule.objects.create(key='DESIGN_UPLOAD_COST', value_type='DECIMAL', decimal_value=0, is_active=True)
        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)

    @patch('services.payment_gateway.ZarinpalGateway.send_request')
    def test_change_design_with_payment(self, mock_send):
        mock_send.return_value = (True, 'https://sandbox.zarinpal.com/pg/StartPay/ABC123', None)
        response = self.api.post(f'/api/campaigns/{self.campaign.id}/change-design/', {
            'design_type': 'CUSTOM_DESIGN',
            'banner_type': self.banner_type.id,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('payment_url', response.data)
        self.assertTrue(CampaignInvoice.objects.filter(modification_type='CHANGE_DESIGN').exists())

    @patch('services.payment_gateway.ZarinpalGateway.send_request')
    def test_extend_campaign(self, mock_send):
        mock_send.return_value = (True, 'https://sandbox.zarinpal.com/pg/StartPay/EXT123', None)
        response = self.api.post(f'/api/campaigns/{self.campaign.id}/extend/', {
            'days': 3
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('payment_url', response.data)
        invoice = CampaignInvoice.objects.get(modification_type='EXTEND')
        self.assertEqual(invoice.modification_data['additional_days'], 3)