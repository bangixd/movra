from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from support.models import SiteSetting, SupportContent

class SupportAPITest(TestCase):
    def setUp(self):
        from support.models import SupportContent
        SupportContent.objects.create(type='CONTACT', title='تماس', body='شماره تماس...')
        self.user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_content(self):
        response = self.client.get('/v1/support/content/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_rules_content(self):
        SupportContent.objects.create(type='RULES', title='قوانین', body='...')
        response = self.client.get('/v1/support/content/?type=RULES')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

class SiteSettingAPITest(TestCase):
    def setUp(self):
        self.setting = SiteSetting.objects.create(
            brand_name="برند تست",
            about_text="توضیحات درباره ما",
            phone="02112345678",
            email="info@test.com",
            social_links={"instagram": "https://instagram.com/test"}
        )
        self.client = APIClient()

    def test_about_api(self):
        response = self.client.get('/v1/support/site-settings/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['brand_name'], 'برند تست')
        self.assertEqual(response.data['phone'], '02112345678')
        self.assertIn('instagram', response.data['social_links'])