from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch
from accounts.models import User
from clients.models import ClientProfile

class ReverseGeocodeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        ClientProfile.objects.create(user=self.user, full_name='Test', national_id='1234567890')
        self.api = APIClient()
        self.api.force_authenticate(user=self.user)

    @patch('services.neshan_client.NeshanClient.reverse_geocode')
    def test_reverse_geocode_success(self, mock_reverse):
        mock_reverse.return_value = {
            'address': 'تهران، خیابان ولیعصر',
            'components': {'city': 'تهران'}
        }
        response = self.api.post('/api/clients/reverse-geocode/', {
            'lat': 35.6892,
            'lng': 51.3890
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('address', response.data)

    def test_reverse_geocode_missing_params(self):
        response = self.api.post('/api/clients/reverse-geocode/', {}, format='json')
        self.assertEqual(response.status_code, 400)