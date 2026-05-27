from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User

class SupportAPITest(TestCase):
    def setUp(self):
        from support.models import SupportContent
        SupportContent.objects.create(type='CONTACT', title='تماس', body='شماره تماس...')
        self.user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_content(self):
        response = self.client.get('/api/support/content/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)