from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from notifications.models import Notification
from campaigns.models import Campaign, CampaignDesign, Template
from brands.models import Brand
from clients.models import ClientProfile
from print_shops.models import PrintShopProfile

class NotificationModelTest(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(phone='09121112233', role=User.Role.DRIVER)
        self.notification = Notification.objects.create(
            recipient=self.driver,
            notification_type=Notification.Type.NEW_CAMPAIGN,
            message='کمپین جدید'
        )

    def test_notification_creation(self):
        self.assertFalse(self.notification.is_read)
        self.assertEqual(self.notification.message, 'کمپین جدید')

class NotificationSignalTest(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(phone='09121112233', role=User.Role.DRIVER)
        self.print_user = User.objects.create_user(phone='09124445566', role=User.Role.PRINT_SHOP)
        self.print_shop = PrintShopProfile.objects.create(user=self.print_user, shop_name='TestPrint', address='A', phone='0')
        self.client_user = User.objects.create_user(phone='09127778899', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='Client', national_id='1234567890')
        self.brand = Brand.objects.create(client=self.client_profile, name='B', slug='b')

    def test_new_campaign_notifies_drivers(self):
        # ایجاد یک کمپین فعال باید برای همه راننده‌ها اعلان بفرستد
        Campaign.objects.create(
            client=self.client_profile,
            slogan='Test',
            brand_name=self.brand,
            start_date='2026-01-01',
            end_date='2026-01-10',
            status=Campaign.Status.ACTIVE
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.driver,
                notification_type=Notification.Type.NEW_CAMPAIGN
            ).exists()
        )

    def test_new_design_assignment_notifies_printshop(self):
        campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='Test',
            brand_name=self.brand,
            start_date='2026-01-01',
            end_date='2026-01-10',
            status=Campaign.Status.ACTIVE
        )
        # طراحی با print_shop اختصاص‌یافته باید اعلان بسازد
        template = Template.objects.create(name='Test Template', variant='test')
        design = CampaignDesign.objects.create(
            campaign=campaign,
            design_type=CampaignDesign.DesignType.DEFAULT_TEMPLATE,
            template=template,
            print_shop=self.print_shop,
            print_status='PENDING'
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.print_user,
                notification_type=Notification.Type.NEW_DESIGN
            ).exists()
        )

class NotificationAPITest(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(phone='09121112233', role=User.Role.DRIVER)
        self.notification = Notification.objects.create(
            recipient=self.driver,
            notification_type=Notification.Type.NEW_CAMPAIGN,
            message='سلام'
        )
        self.api = APIClient()
        self.api.force_authenticate(user=self.driver)

    def test_list_notifications(self):
        response = self.api.get('/v1/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_mark_notification_read(self):
        response = self.api.post(f'/v1/notifications/{self.notification.id}/read/')
        # اول مطمئن شو که درخواست موفق بوده
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # حالا شیء را از نو بخوان
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_read(self):
        Notification.objects.create(recipient=self.driver, notification_type=Notification.Type.NEW_DESIGN, message='hi')
        response = self.api.post('/v1/notifications/read_all/')
        self.assertEqual(Notification.objects.filter(recipient=self.driver, is_read=True).count(), 2)