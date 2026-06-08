from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from clients.models import ClientProfile

class ClientProfileAPITest(TestCase):
    def setUp(self):
        print("\n========== CLIENT API SETUP ==========")
        self.client_user = User.objects.create_user(phone='09121112233', role=User.Role.CLIENT)
        self.other_client = User.objects.create_user(phone='09121114455', role=User.Role.CLIENT)
        self.other_client.is_staff = False
        self.other_client.save()
        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)
        response = self.api.options('/v1/clients/documents/')
        print(response['Allow'])  # باید POST, GET, OPTIONS, ... را نشان دهد

        self.profile = ClientProfile.objects.create(
            user=self.client_user,
            advertiser_type=ClientProfile.AdvertiserType.REAL,
            full_name='Sara Ahmadi',
            national_id='9876543210',
        )
        print(f"✅ Setup complete: Client={self.client_user.phone}, Profile={self.profile.full_name}")

    def test_get_own_profile(self):
        print("\n--- TEST: Get Own Profile ---")
        response = self.api.get(f'/v1/clients/{self.profile.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['full_name'], 'Sara Ahmadi')
        print("✅ Own profile retrieved")

    def test_cannot_get_other_profile(self):
        print("\n--- TEST: Cannot Get Other Profile ---")
        other_profile = ClientProfile.objects.create(
            user=self.other_client,
            advertiser_type=ClientProfile.AdvertiserType.LEGAL,
            company_name='Other Inc.',
        )
        response = self.api.get(f'/v1/clients/{other_profile.id}/')
        self.assertEqual(response.status_code, 403)
        print("✅ Other profile not visible")

    def test_create_profile(self):
        print("\n--- TEST: Create Profile ---")
        self.profile.delete()
        response = self.api.post('/v1/clients/', {
            'advertiser_type': 'REAL',
            'full_name': 'New Client',
            'national_id': '1112223330',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ClientProfile.objects.filter(user=self.client_user).count(), 1)
        print("✅ Profile created via API")

    def test_update_profile(self):
        print("\n--- TEST: Update Profile ---")
        response = self.api.patch(f'/v1/clients/{self.profile.id}/', {
            'full_name': 'Sara Updated',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, 'Sara Updated')
        print("✅ Profile updated")

    def test_non_client_cannot_create(self):
        print("\n--- TEST: Non-Client Cannot Create ---")
        driver_user = User.objects.create_user(phone='09120007788', role=User.Role.DRIVER)
        self.api.force_authenticate(user=driver_user)
        response = self.api.post('/v1/clients/', {
            'advertiser_type': 'REAL',
            'full_name': 'Invalid',
            'national_id': '0000000000',
        }, format='json')
        self.assertEqual(response.status_code, 403)
        print("✅ Non-client blocked")