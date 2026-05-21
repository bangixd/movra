from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from drivers.models import DriverProfile, DriverDocument
from vehicles.models import VehicleType

class DriverProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)

    def test_create_driver_profile(self):
        profile = DriverProfile.objects.create(
            user=self.user,
            full_name='Ali Rezaei',
            national_id='1234567890',
            vehicle_type=self.vehicle_type,
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.kyc_status, 'NOT_STARTED')
        self.assertIsNone(profile.kyc_submitted_at)
        self.assertIsNone(profile.kyc_reviewed_at)

    def test_string_representation(self):
        profile = DriverProfile.objects.create(
            user=self.user,
            full_name='Ali',
            national_id='1234567890',
            vehicle_type=self.vehicle_type,
        )
        self.assertIn(self.user.phone, str(profile))

    def test_driver_profile_optional_fields(self):
        profile = DriverProfile.objects.create(
            user=self.user,
            full_name='Ali',
            national_id='1234567890',
            vehicle_type=self.vehicle_type,
            birth_date='1990-01-01',
            gender='MALE',
            father_name='Reza',
        )
        self.assertEqual(profile.gender, 'MALE')
        self.assertEqual(profile.father_name, 'Reza')

    def test_share_location_default_true(self):
        profile = DriverProfile.objects.create(
            user=self.user,
            full_name='Ali',
            national_id='1234567890',
            vehicle_type=self.vehicle_type,
        )
        self.assertTrue(profile.share_location)

class DriverDocumentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)

    def test_create_document(self):
        doc = DriverDocument.objects.create(
            user=self.user,
            document_type=DriverDocument.DocumentType.NATIONAL_ID_FRONT,
            status=DriverDocument.ApprovalStatus.PENDING,
        )
        self.assertEqual(doc.user, self.user)
        self.assertEqual(doc.status, DriverDocument.ApprovalStatus.PENDING)
        self.assertEqual(doc.document_type, DriverDocument.DocumentType.NATIONAL_ID_FRONT)