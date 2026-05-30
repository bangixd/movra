# clients/tests_profile.py
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User, ClientProfile
from brands.models import Brand
from campaigns.models import Campaign
from wallet.models import Wallet

class ClientProfileTest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.profile = ClientProfile.objects.create(user=self.client_user, full_name='Sara', national_id='1234567890')
        self.wallet = Wallet.objects.get(user=self.client_user)
        self.wallet.balance = 50000
        self.wallet.save()
        self.brand = Brand.objects.create(client=self.profile, name='B', slug='b')
        Campaign.objects.create(client=self.profile, brand_name=self.brand, status=Campaign.Status.ACTIVE, slogan='C1', start_date=date.today())
        Campaign.objects.create(client=self.profile, brand_name=self.brand, status=Campaign.Status.PAUSED, slogan='C2', start_date=date.today())
        Campaign.objects.create(client=self.profile, brand_name=self.brand, status=Campaign.Status.COMPLETED, slogan='C3', start_date=date.today())
        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)

    def test_profile_fields(self):
        response = self.api.get(f'/api/clients/profile/{self.profile.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data['wallet_balance'], '50000.00')
        self.assertEqual(data['active_campaigns_count'], 2)  # ACTIVE و PAUSED

    def test_my_profile_me_endpoint(self):
        response = self.api.get('/api/clients/profile/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['full_name'], 'Sara')

    def test_update_my_profile(self):
        response = self.api.patch('/api/clients/profile/me/', {'full_name': 'سارا جدید'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, 'سارا جدید')