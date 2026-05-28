from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from .models import FAQCategory, FAQItem, SiteSetting, Ticket

class AdminAPITest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(phone='09990000000', password='admin')
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_create_faq_category(self):
        response = self.client.post('/api/support/admin/faq-categories/', {
            'name': 'عمومی',
            'order': 1
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(FAQCategory.objects.filter(name='عمومی').exists())

    def test_update_site_setting(self):
        SiteSetting.objects.create(brand_name='قدیمی')
        response = self.client.patch('/api/support/admin/site-settings/1/', {
            'brand_name': 'جدید'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SiteSetting.objects.first().brand_name, 'جدید')

    def test_list_tickets(self):
        driver = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        Ticket.objects.create(user=driver, subject='تست', name='علی', phone='09120001122', message='...')
        response = self.client.get('/api/support/admin/tickets/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_non_admin_cannot_create_faq(self):
        user = User.objects.create_user(phone='09120000000', role=User.Role.DRIVER)
        self.client.force_authenticate(user=user)
        response = self.client.post('/api/support/admin/faq-categories/', {
            'name': 'غیرمجاز',
            'order': 1
        }, format='json')
        self.assertEqual(response.status_code, 403)