from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from django.contrib.gis.geos import Point
from accounts.models import User
from drivers.models import DriverProfile, DriverDocument
from geo.models import Province, City
from vehicles.models import VehicleType


class DriverRegistrationE2ETest(TestCase):
    """
    تست جامع جریان ثبت‌نام راننده (۴ مرحله):
    ۱. اطلاعات شخصی
    ۲. بارگذاری مدارک
    ۳. تأیید ادمین
    ۴. پذیرش قرارداد
    """

    def setUp(self):
        print("\n========== Driver E2E Test Setup ==========")

        # Admin
        self.admin = User.objects.create_superuser(phone='09990000000', password='admin')

        # Driver user
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)

        # Province & City (for step 1)
        self.province = Province.objects.create(name='Tehran')
        self.city = City.objects.create(
            name='Tehran City',
            province=self.province,
            center=Point(51.38, 35.68, srid=4326)
        )

        # VehicleType (needed for profile)
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)

        # API Clients
        self.driver_api = APIClient()
        self.driver_api.force_authenticate(user=self.driver_user)

        self.admin_api = APIClient()
        self.admin_api.force_authenticate(user=self.admin)

        print("✅ Setup complete")

    # ================================================================
    # STEP 1: Personal Information
    # ================================================================
    def test_step1_submit_personal_info(self):
        """
        مرحلهٔ ۱: ارسال اطلاعات شخصی (نام، کد ملی، تاریخ تولد، شهر)
        انتظار: registration_step = DOCUMENTS (2)
        """
        print("\n--- TEST: Step 1 - Personal Information ---")

        # Create initial profile (or use the one created by signal)
        profile, _ = DriverProfile.objects.get_or_create(
            user=self.driver_user,
            defaults={'registration_step': DriverProfile.RegistrationStep.PERSONAL_INFO}
        )
        profile.registration_step = DriverProfile.RegistrationStep.PERSONAL_INFO
        profile.save()

        response = self.driver_api.patch(f'/v1/drivers/profile/{profile.id}/', {
            'full_name': 'Ali Rezaei',
            'national_id': '1234567890',
            'birth_date': '1990-01-01',
            'city': self.city.id
        }, format='json')

        print(f"   Status: {response.status_code}")
        print(f"   Data: {response.data}")

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.registration_step, DriverProfile.RegistrationStep.DOCUMENTS)
        self.assertEqual(profile.full_name, 'Ali Rezaei')
        print("✅ Step 1 completed: registration_step = DOCUMENTS")

    # ================================================================
    # STEP 2: Upload Documents
    # ================================================================
    def test_step2_upload_documents(self):
        """
        مرحلهٔ ۲: آپلود مدارک (گواهینامه، کارت خودرو، برگه سبز)
        انتظار: registration_step = VERIFICATION (3)
        """
        print("\n--- TEST: Step 2 - Upload Documents ---")

        # Set profile to step 2
        profile, _ = DriverProfile.objects.get_or_create(
            user=self.driver_user,
            defaults={'registration_step': DriverProfile.RegistrationStep.DOCUMENTS}
        )
        profile.registration_step = DriverProfile.RegistrationStep.DOCUMENTS
        profile.save()

        from django.core.files.uploadedfile import SimpleUploadedFile

        # Upload Driving License
        fake_file = SimpleUploadedFile("license.jpg", b"file_content", content_type="image/jpeg")
        response = self.driver_api.post('/v1/drivers/documents/', {
            'document_type': 'DRIVING_LICENSE',
            'file': fake_file
        }, format='multipart')

        print(f"   Upload Status: {response.status_code}")
        print(f"   Upload Data: {response.data}")

        self.assertEqual(response.status_code, 201)
        profile.refresh_from_db()
        self.assertEqual(profile.registration_step, DriverProfile.RegistrationStep.VERIFICATION)
        self.assertIsNotNone(profile.kyc_submitted_at)
        self.assertEqual(DriverDocument.objects.filter(user=self.driver_user).count(), 1)
        print("✅ Step 2 completed: registration_step = VERIFICATION")

    # ================================================================
    # STEP 3: Admin Review (Approve)
    # ================================================================
    def test_step3_admin_approval(self):
        """
        مرحلهٔ ۳: ادمین مدارک را تأیید می‌کند
        انتظار: kyc_status = APPROVED, registration_step = CONTRACT (4)
        """
        print("\n--- TEST: Step 3 - Admin Approval ---")

        # Set profile to step 3
        profile, _ = DriverProfile.objects.get_or_create(
            user=self.driver_user,
            defaults={'registration_step': DriverProfile.RegistrationStep.VERIFICATION}
        )
        profile.registration_step = DriverProfile.RegistrationStep.VERIFICATION
        profile.save()

        # Create a pending document
        doc = DriverDocument.objects.create(
            user=self.driver_user,
            document_type='DRIVING_LICENSE',
            file='drivers/documents/test.jpg',
            status=DriverDocument.ApprovalStatus.PENDING
        )
        print(f"   Document created: id={doc.id}, status={doc.status}")

        # Admin approves
        response = self.admin_api.patch(f'/v1/drivers/documents/{doc.id}/review/', {
            'status': 'APPROVED'
        }, format='json')

        print(f"   Review Status: {response.status_code}")
        print(f"   Review Data: {response.data}")

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'APPROVED')
        self.assertEqual(profile.kyc_status, 'APPROVED')
        self.assertEqual(profile.registration_step, DriverProfile.RegistrationStep.CONTRACT)
        print("✅ Step 3 completed: kyc_status = APPROVED, registration_step = CONTRACT")

    # ================================================================
    # STEP 3 (Alternative): Admin Rejects
    # ================================================================
    def test_step3_admin_rejection(self):
        """
        مرحلهٔ ۳: ادمین مدرک را رد می‌کند
        انتظار: kyc_status = REJECTED, registration_step همچنان VERIFICATION
        """
        print("\n--- TEST: Step 3 - Admin Rejection ---")

        profile, _ = DriverProfile.objects.get_or_create(
            user=self.driver_user,
            defaults={'registration_step': DriverProfile.RegistrationStep.VERIFICATION}
        )
        profile.registration_step = DriverProfile.RegistrationStep.VERIFICATION
        profile.save()

        doc = DriverDocument.objects.create(
            user=self.driver_user,
            document_type='DRIVING_LICENSE',
            file='test.jpg',
            status=DriverDocument.ApprovalStatus.PENDING
        )

        response = self.admin_api.patch(f'/v1/drivers/documents/{doc.id}/review/', {
            'status': 'REJECTED',
            'reject_reason': 'عکس ناخوانا است'
        }, format='json')

        print(f"   Status: {response.status_code}, Data: {response.data}")

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        doc.refresh_from_db()
        self.assertEqual(doc.status, 'REJECTED')
        self.assertEqual(doc.reject_reason, 'عکس ناخوانا است')
        self.assertEqual(profile.kyc_status, 'REJECTED')
        print("✅ Step 3 rejected: kyc_status = REJECTED")

    # ================================================================
    # STEP 4: Accept Contract
    # ================================================================
    def test_step4_accept_contract(self):
        """
        مرحلهٔ ۴: پذیرش قرارداد
        انتظار: is_contract_accepted = True
        """
        print("\n--- TEST: Step 4 - Accept Contract ---")

        profile, _ = DriverProfile.objects.get_or_create(
            user=self.driver_user,
            defaults={'registration_step': DriverProfile.RegistrationStep.CONTRACT}
        )
        profile.registration_step = DriverProfile.RegistrationStep.CONTRACT
        profile.kyc_status = 'APPROVED'
        profile.save()

        response = self.driver_api.patch('/v1/drivers/profile/accept_contract/')
        print(f"   Status: {response.status_code}, Data: {response.data}")

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertTrue(profile.is_contract_accepted)
        print("✅ Step 4 completed: is_contract_accepted = True")

    # ================================================================
    # STEP 4 (Fail): Accept without approval
    # ================================================================
    def test_step4_accept_contract_without_approval(self):
        """
        تلاش برای پذیرش قرارداد بدون تأیید احراز هویت
        انتظار: خطای ۴۰۰
        """
        print("\n--- TEST: Step 4 - Accept Contract Without Approval ---")

        profile, _ = DriverProfile.objects.get_or_create(
            user=self.driver_user,
            defaults={'registration_step': DriverProfile.RegistrationStep.CONTRACT}
        )
        profile.registration_step = DriverProfile.RegistrationStep.CONTRACT
        profile.kyc_status = 'PENDING'  # ← هنوز تأیید نشده
        profile.save()

        response = self.driver_api.patch('/v1/drivers/profile/accept_contract/')
        print(f"   Status: {response.status_code}, Data: {response.data}")

        self.assertEqual(response.status_code, 400)
        self.assertIn('ابتدا باید احراز هویت', response.data.get('error', ''))
        print("✅ Contract rejected: kyc_status not APPROVED")