from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from clients.models import ClientProfile, ClientDocument

class ClientDocumentAPITest(TestCase):
    def setUp(self):
        print("\n========== CLIENT DOCUMENT API SETUP ==========")
        # کاربر کلاینت
        self.client_user = User.objects.create_user(phone='09121112233', role=User.Role.CLIENT)
        # ادمین
        self.admin = User.objects.create_superuser(phone='09990000000', password='adminpass')

        # ساخت پروفایل کلاینت (برای عملکرد سیگنال)
        self.profile = ClientProfile.objects.create(
            user=self.client_user,
            advertiser_type=ClientProfile.AdvertiserType.REAL,
            full_name='Sara Ahmadi',
            national_id='1234567890',
        )

        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)
        print("✅ Client & admin ready")

    def test_upload_document(self):
        print("\n--- TEST: Upload Document ---")
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("doc.jpg", b"file_content", content_type="image/jpeg")
        response = self.api.post('/api/clients/documents/', {
            'document_type': 'NATIONAL_ID',
            'file': file,
        }, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ClientDocument.objects.count(), 1)
        print("✅ Document uploaded")

    def test_admin_review(self):
        print("\n--- TEST: Admin Review ---")
        # یک مدرک با وضعیت PENDING بسازیم
        doc = ClientDocument.objects.create(
            user=self.client_user,
            document_type='COMPANY_REGISTRATION',
            file='clients/documents/test.jpg',
            status=ClientDocument.ApprovalStatus.PENDING
        )
        # احراز هویت با ادمین
        self.api.force_authenticate(user=self.admin)
        response = self.api.patch(f'/api/clients/documents/{doc.id}/review/', {
            'status': 'APPROVED',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'APPROVED')
        print("✅ Admin approved document")

    def test_non_client_cannot_upload(self):
        print("\n--- TEST: Non-Client Cannot Upload ---")
        driver_user = User.objects.create_user(phone='09120000000', role=User.Role.DRIVER)
        self.api.force_authenticate(user=driver_user)
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("doc.jpg", b"file_content", content_type="image/jpeg")
        response = self.api.post('/api/clients/documents/', {
            'document_type': 'NATIONAL_ID',
            'file': file,
        }, format='multipart')
        self.assertEqual(response.status_code, 403)
        print("✅ Non-client blocked")