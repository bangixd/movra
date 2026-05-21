from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from drivers.models import DriverProfile
from .models import VehicleType, Vehicle

class VehicleModelTest(TestCase):
    def setUp(self):
        self.driver_user = User.objects.create_user(phone='09121111111', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(user=self.driver_user, full_name='Driver1', national_id='1234567890')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)

    def test_vehicle_hourly_rate_from_type(self):
        vehicle = Vehicle.objects.create(
            driver=self.driver_profile,
            vehicle_type=self.vehicle_type,
            plate_number='12A345B67',
            banner_max_width_cm=150,
            banner_max_height_cm=80
        )
        self.assertEqual(vehicle.hourly_rate, 50000)
        # تغییر نرخ نوع خودرو باید روی نرخ خودرو تأثیر بگذارد
        self.vehicle_type.base_hourly_rate = 60000
        self.vehicle_type.save()
        self.assertEqual(vehicle.hourly_rate, 60000)

class VehicleAPITest(TestCase):
    def setUp(self):
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(user=self.driver_user, full_name='Ali', national_id='1234567890')
        self.vehicle_type = VehicleType.objects.create(name='SUV', base_hourly_rate=80000)
        self.api = APIClient()
        self.api.force_authenticate(user=self.driver_user)

    def test_create_vehicle(self):
        response = self.api.post('/api/vehicles/', {
            'vehicle_type': self.vehicle_type.id,
            'plate_number': '11B222C33',
            'banner_max_width_cm': 200,
            'banner_max_height_cm': 100,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        vehicle = Vehicle.objects.get(plate_number='11B222C33')
        self.assertEqual(vehicle.driver, self.driver_profile)

    def test_only_own_vehicles_listed(self):
        other_driver = User.objects.create_user(phone='09120003344', role=User.Role.DRIVER)
        other_profile = DriverProfile.objects.create(user=other_driver, full_name='Hossein', national_id='9999999999')
        Vehicle.objects.create(driver=self.driver_profile, vehicle_type=self.vehicle_type, plate_number='X', banner_max_width_cm=100, banner_max_height_cm=50)
        Vehicle.objects.create(driver=other_profile, vehicle_type=self.vehicle_type, plate_number='Y', banner_max_width_cm=100, banner_max_height_cm=50)
        response = self.api.get('/api/vehicles/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['plate_number'], 'X')