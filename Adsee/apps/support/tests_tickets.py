from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from .models import Ticket

class TicketAPITest(TestCase):
    def setUp(self):
        self.driver = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.client = APIClient()
        self.client.force_authenticate(user=self.driver)

    def test_create_ticket(self):
        response = self.client.post('/api/support/tickets/', {
            'subject': 'مشکل در ثبت‌نام',
            'name': 'علی رضایی',
            'phone': '09120001122',
            'message': 'توضیحات مشکل...'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Ticket.objects.filter(user=self.driver).exists())

    def test_list_tickets(self):
        Ticket.objects.create(user=self.driver, subject='تست', name='علی', phone='09120001122', message='...')
        response = self.client.get('/api/support/tickets/list/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)