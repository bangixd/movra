from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from drivers.models import DriverProfile, DriverDocument
from vehicles.models import VehicleType
from unittest.mock import patch
from services.tasks import process_driver_document

class DriverDocumentAPITest(TestCase):
    def setUp(self):
        print("\n========== DRIVER DOCUMENT API SETUP ==========")
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.admin = User.objects.create_superuser(phone='09990000000', password='admin')
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        DriverProfile.objects.create(user=self.driver_user, full_name='Ali', national_id='1234567890')
        # ساخت پروفایل راننده (ضروری برای سیگنال)
        self.api = APIClient()
        self.api.force_authenticate(user=self.driver_user)
        print("✅ Driver & admin ready")

    def test_upload_document(self):
        print("\n--- TEST: Upload Document ---")
        # شبیه‌سازی فایل
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("doc.jpg", b"file_content", content_type="image/jpeg")
        response = self.api.post('/api/drivers/documents/', {
            'document_type': 'NATIONAL_ID_FRONT',
            'file': file,
        }, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(DriverDocument.objects.count(), 1)
        print("✅ Document uploaded")

    def test_admin_review(self):
        print("\n--- TEST: Admin Review ---")
        doc = DriverDocument.objects.create(
            user=self.driver_user,
            document_type='DRIVING_LICENSE',
            file='drivers/documents/test.jpg',
            status=DriverDocument.ApprovalStatus.PENDING
        )
        self.api.force_authenticate(user=self.admin)
        response = self.api.patch(f'/api/drivers/documents/{doc.id}/review/', {
            'status': 'APPROVED',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'APPROVED')
        print("✅ Admin approved document")

    def test_non_driver_cannot_upload(self):
        print("\n--- TEST: Non-Driver Cannot Upload ---")
        normal_user = User.objects.create_user(phone='09120000000', role=User.Role.CLIENT)
        self.api.force_authenticate(user=normal_user)
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("doc.jpg", b"file_content", content_type="image/jpeg")
        response = self.api.post('/api/drivers/documents/', {
            'document_type': 'NATIONAL_ID_FRONT',
            'file': file,
        }, format='multipart')
        self.assertEqual(response.status_code, 403)
        print("✅ Non-driver blocked")


    @patch('services.tasks.process_driver_document.delay')
    def test_celery_task_called_on_upload(self, mock_delay):
        doc = DriverDocument.objects.create(
            user=self.driver_user,
            document_type='NATIONAL_ID_FRONT',
            file='drivers/documents/test.jpg'
        )
        self.assertTrue(mock_delay.called)
        mock_delay.assert_called_with(doc.id)

