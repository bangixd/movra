from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from drivers.models import DriverProfile, DriverDocument
from geo.models import Province, City
from django.contrib.gis.geos import Point

class DriverRegistrationFlowTest(TestCase):
    def setUp(self):
        # ادمین
        self.admin = User.objects.create_superuser(phone='09990000000', password='admin')
        # راننده
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.client = APIClient()
        self.client.force_authenticate(user=self.driver_user)

        # استان و شهر
        self.province = Province.objects.create(name='تهران')
        self.city = City.objects.create(name='تهران', province=self.province, center=Point(51.38, 35.68, srid=4326))

        # پروفایل اولیه (باید خودکار ساخته شود یا در سیگنال؟)
        # فرض می‌کنیم با اولین PATCH ساخته می‌شود یا از قبل سیگنال داریم.
        # برای تست، پروفایل را دستی می‌سازیم
        self.profile = DriverProfile.objects.create(user=self.driver_user, registration_step=1)

    def test_step1_submit_personal_info(self):
        """مرحله ۱: تکمیل اطلاعات شخصی"""
        response = self.client.patch(f'/api/drivers/profile/{self.profile.id}/', {
            'full_name': 'رضایی علی',
            'national_id': '1234567890',
            'birth_date': '1990-01-01',
            'city': self.city.id
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.registration_step, 2)  # به مرحله مدارک رفت

    def test_step2_upload_documents(self):
        """مرحله ۲: بارگذاری مدارک و انتقال به مرحله ۳"""
        # ابتدا مرحله ۱ را پاس کنیم
        self.profile.registration_step = 2
        self.profile.save()

        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("doc.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.post('/api/drivers/documents/', {
            'document_type': 'DRIVING_LICENSE',
            'file': file
        }, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.registration_step, 3)

    def test_step3_admin_approval(self):
        """مرحله ۳: ادمین مدارک را تأیید می‌کند و به مرحله ۴ می‌رود"""
        # یک مدرک آپلود کنیم
        doc = DriverDocument.objects.create(
            user=self.driver_user,
            document_type='DRIVING_LICENSE',
            file='drivers/documents/test.jpg',
            status=DriverDocument.ApprovalStatus.PENDING
        )
        self.profile.registration_step = 3
        self.profile.save()

        # ادمین وارد شود
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(f'/api/drivers/documents/{doc.id}/review/', {
            'status': 'APPROVED'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.kyc_status, 'APPROVED')
        self.assertEqual(self.profile.registration_step, 4)

    def test_step4_accept_contract(self):
        """مرحله ۴: پذیرش قرارداد"""
        self.profile.registration_step = 4
        self.profile.kyc_status = 'APPROVED'
        self.profile.save()

        self.client.force_authenticate(user=self.driver_user)
        response = self.client.patch('/api/drivers/profile/accept_contract/')
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_contract_accepted)
        self.assertEqual(self.profile.registration_step, 4)