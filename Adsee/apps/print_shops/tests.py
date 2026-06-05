from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.gis.geos import Point
from accounts.models import User
from print_shops.models import PrintShopProfile
from campaigns.models import CampaignDesign, Campaign
from brands.models import Brand
from clients.models import ClientProfile
from vehicles.models import VehicleType
from campaigns.models import Template



class PrintShopModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone='09120001122', role=User.Role.PRINT_SHOP)
        self.profile = PrintShopProfile.objects.create(
            user=self.user,
            shop_name='چاپخانه تست',
            address='تهران، خیابان ولیعصر',
            phone='02112345678',
            location=Point(51.38, 35.68, srid=4326)
        )

    def test_profile_creation(self):
        self.assertEqual(self.profile.shop_name, 'چاپخانه تست')
        self.assertEqual(self.profile.user, self.user)

    def test_string_representation(self):
        self.assertEqual(str(self.profile), 'چاپخانه تست')


class PrintShopAPITest(TestCase):
    def setUp(self):
        # کاربر چاپخانه
        self.print_user = User.objects.create_user(phone='09120001122', role=User.Role.PRINT_SHOP)
        self.print_api = APIClient()
        self.print_api.force_authenticate(user=self.print_user)

        # کاربر راننده (نباید بتواند پروفایل چاپخانه بسازد)
        self.driver_user = User.objects.create_user(phone='09123334455', role=User.Role.DRIVER)
        self.driver_api = APIClient()
        self.driver_api.force_authenticate(user=self.driver_user)

        # داده‌های کمپین و طراحی برای تست ارجاع طرح
        self.client_user = User.objects.create_user(phone='09125556666', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user, full_name='Client', national_id='1234567890'
        )
        self.brand = Brand.objects.create(client=self.client_profile, name='Brand', slug='b')
        self.campaign = Campaign.objects.create(
            client=self.client_profile, slogan='Camp', brand_name=self.brand,
            start_date='2026-01-01', end_date='2026-01-10', status=Campaign.Status.ACTIVE
        )
        self.template = Template.objects.create(name='Test Template', variant='test')
        self.design = CampaignDesign.objects.create(
            campaign=self.campaign,
            design_type=CampaignDesign.DesignType.DEFAULT_TEMPLATE,
            template=self.template,
            status=CampaignDesign.DesignStatus.PENDING
        )

    def test_create_printshop_profile(self):
        response = self.print_api.post('/api/print_shops/profile/', {
            'shop_name': 'چاپخانه جدید',
            'address': 'مشهد',
            'phone': '05112345678',
            'location': 'POINT(59.6 36.3)'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(PrintShopProfile.objects.count(), 1)

    def test_non_printshop_cannot_create_profile(self):
        response = self.driver_api.post('/api/print_shops/profile/', {
            'shop_name': 'چاپخانه متفرقه',
            'address': 'اینجا',
            'phone': '09120000000'
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_assigned_designs_list(self):
        # اختصاص یک طرح به چاپخانه
        shop = PrintShopProfile.objects.create(user=self.print_user, shop_name='Test', address='A', phone='0')
        self.design.print_shop = shop
        self.design.save()

        response = self.print_api.get('/api/print_shops/designs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.design.id)

    def test_update_design_print_status(self):
        shop = PrintShopProfile.objects.create(user=self.print_user, shop_name='Test', address='A', phone='0')
        self.design.print_shop = shop
        self.design.save()

        # چاپخانه وضعیت را تغییر دهد
        response = self.print_api.patch(f'/api/print_shops/designs/{self.design.id}/status/', {
            'print_status': 'ACCEPTED',
            'estimated_ready_date': '2026-05-25T10:00:00Z'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.design.refresh_from_db()
        self.assertEqual(self.design.print_status, 'ACCEPTED')