from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from drivers.models import DriverProfile
from vehicles.models import VehicleType

class DriverProfileAPITest(TestCase):
    def setUp(self):
        print("\n========== DRIVER API SETUP ==========")
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.other_driver = User.objects.create_user(phone='09120003344', role=User.Role.DRIVER)
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)

        self.api = APIClient()
        self.api.force_authenticate(user=self.driver_user)

        # ساخت یک پروفایل برای driver_user
        self.profile = DriverProfile.objects.create(
            user=self.driver_user,
            full_name='Ali Rezaei',
            national_id='1234567890',
            vehicle_type=self.vehicle_type,
        )
        print(f"✅ Setup complete: Driver={self.driver_user.phone}, Profile={self.profile.full_name}")

    def test_get_own_profile(self):
        print("\n--- TEST: Get Own Profile ---")
        response = self.api.get(f'/api/drivers/{self.profile.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['full_name'], 'Ali Rezaei')
        print("✅ Own profile retrieved")

    def test_cannot_get_other_profile(self):
        print("\n--- TEST: Cannot Get Other Profile ---")
        other_profile = DriverProfile.objects.create(
            user=self.other_driver,
            full_name='Other Driver',
            national_id='1111111111',
            vehicle_type=self.vehicle_type,
        )
        response = self.api.get(f'/api/drivers/{other_profile.id}/')
        self.assertEqual(response.status_code, 403)
        print("✅ Other profile not visible")

    def test_create_profile(self):
        print("\n--- TEST: Create Profile ---")
        # پروفایل فعلی را حذف می‌کنیم تا دوباره ایجاد کنیم (چون OneToOne است)
        self.profile.delete()
        response = self.api.post('/api/drivers/', {
            'full_name': 'Hossein',
            'national_id': '1231231230',
            'vehicle_type': self.vehicle_type.id,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(DriverProfile.objects.filter(user=self.driver_user).count(), 1)
        print("✅ Profile created via API")

    def test_update_profile(self):
        print("\n--- TEST: Update Profile ---")
        response = self.api.patch(f'/api/drivers/{self.profile.id}/', {
            'full_name': 'Ali Updated',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, 'Ali Updated')
        print("✅ Profile updated")

    def test_non_driver_cannot_create(self):
        print("\n--- TEST: Non-Driver Cannot Create ---")
        normal_user = User.objects.create_user(phone='09120005566', role=User.Role.CLIENT)
        self.api.force_authenticate(user=normal_user)
        response = self.api.post('/api/drivers/', {
            'full_name': 'Invalid',
            'national_id': '0000000000',
            'vehicle_type': self.vehicle_type.id,
        }, format='json')
        self.assertEqual(response.status_code, 403)
        print("✅ Non-driver blocked")