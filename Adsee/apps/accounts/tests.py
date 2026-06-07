from datetime import timedelta
from clients.models import ClientProfile
from drivers.models import DriverProfile
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from accounts.models import OTP, User


class UserModelTest(TestCase):
    def test_create_user_with_phone(self):
        user = User.objects.create_user(phone='09123456789')
        self.assertEqual(user.phone, '09123456789')
        self.assertTrue(user.has_usable_password() is False)  # کاربر عادی پسورد ندارد
        self.assertEqual(user.role, User.Role.CLIENT)         # نقش پیش‌فرض

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(phone='09990001111', password='Admin123')
        self.assertTrue(superuser.has_usable_password())
        self.assertEqual(superuser.role, User.Role.ADMIN)


class ProfileModelTest(TestCase):
    def setUp(self):
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.client_user = User.objects.create_user(phone='09130001133', role=User.Role.CLIENT)

    def test_driver_profile_creation(self):
        profile = DriverProfile.objects.create(user=self.driver_user, full_name='Ali', national_id='1234567890')
        self.assertEqual(profile.kyc_status, 'PENDING')
        self.assertIsNone(profile.kyc_submitted_at)

    def test_client_profile_creation(self):
        profile = ClientProfile.objects.create(
            user=self.client_user,
            advertiser_type=ClientProfile.AdvertiserType.REAL,
            full_name='Sara',
            national_id='9876543210'
        )
        self.assertEqual(profile.kyc_status, 'PENDING')


class OTPTest(TestCase):
    def test_otp_expiry(self):
        otp = OTP.objects.create(
            identifier='09120000000',
            purpose=OTP.Purpose.LOGIN,
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        self.assertFalse(otp.is_expired())
        otp.expires_at = timezone.now() - timedelta(seconds=1)
        otp.save()
        self.assertTrue(otp.is_expired())

class OTPRequestTest(TestCase):
    def setUp(self):
        print("\n========== SETUP OTP TESTS ==========")
        self.api = APIClient()
        self.url = '/v1/auth/otp/'
        self.verify_url = '/v1/auth/otp/verify/'
        self.phone = '09121111111'
        print(f"✅ API Client ready – endpoint: {self.url}")

    # ---------------------------------------------------------------
    @patch('accounts.services.otp_service.OTPService.send_otp_sms')
    def test_request_otp_new_user(self, mock_send):
        """درخواست OTP برای کاربر جدید – باید ۲۰۰ برگرداند و کاربر ساخته شود"""
        print("\n--- TEST: Request OTP – New User ---")
        mock_send.return_value = None  # شبیه‌سازی موفقیت ارسال پیامک

        response = self.api.post(self.url, {
            'identifier': self.phone,
            'purpose': 'REGISTER'
        }, format='json')

        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.data}")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(phone=self.phone).exists())
        self.assertTrue(OTP.objects.filter(identifier=self.phone, purpose='REGISTER').exists())
        print("✅ New user created & OTP stored")

    # ---------------------------------------------------------------
    @patch('accounts.services.otp_service.OTPService.send_otp_sms')
    def test_request_otp_existing_user(self, mock_send):
        """درخواست OTP برای کاربر موجود – باید OTP جدید جایگزین قبلی شود"""
        print("\n--- TEST: Request OTP – Existing User ---")
        mock_send.return_value = None

        # ابتدا کاربر را بسازیم
        User.objects.create_user(phone=self.phone, is_active=True)
        # یک OTP قدیمی برای این کاربر
        old_otp = OTP.objects.create(
            identifier=self.phone,
            purpose='LOGIN',
            code='111111',
            expires_at=timezone.now() + timezone.timedelta(minutes=2)
        )
        print(f"   Old OTP created: {old_otp.code}")

        response = self.api.post(self.url, {
            'identifier': self.phone,
            'purpose': 'LOGIN'
        }, format='json')

        print(f"   Status: {response.status_code}")
        print(f"   OTPs count: {OTP.objects.filter(identifier=self.phone, purpose='LOGIN', used=False).count()}")

        self.assertEqual(response.status_code, 200)
        # OTP قدیمی باید حذف شده باشد و فقط یک OTP جدید باقی بماند
        self.assertEqual(OTP.objects.filter(identifier=self.phone, purpose='LOGIN', used=False).count(), 1)
        self.assertNotEqual(OTP.objects.first().code, '111111')
        print("✅ Old OTP replaced with new one")

    # ---------------------------------------------------------------
    def test_request_otp_missing_field(self):
        """درخواست OTP بدون فیلد اجباری – باید ۴۰۰ برگرداند"""
        print("\n--- TEST: Request OTP – Missing Field ---")
        response = self.api.post(self.url, {}, format='json')
        print(f"   Status: {response.status_code}")
        print(f"   Errors: {response.data}")
        self.assertEqual(response.status_code, 400)
        print("✅ Validation error returned")


class OTPVerifyTest(TestCase):
    def setUp(self):
        print("\n========== SETUP VERIFY TESTS ==========")
        self.api = APIClient()
        self.url = '/v1/auth/otp/verify/'
        self.phone = '09121111111'
        self.user = User.objects.create_user(phone=self.phone, is_active=True)
        print(f"✅ User created: {self.phone}")

    # ---------------------------------------------------------------
    def test_verify_otp_success_login(self):
        """تأیید OTP موفق – باید توکن برگرداند"""
        print("\n--- TEST: Verify OTP – Success (LOGIN) ---")
        # ایجاد یک OTP معتبر
        otp = OTP.objects.create(
            identifier=self.phone,
            purpose='LOGIN',
            code='123456',
            expires_at=timezone.now() + timezone.timedelta(minutes=5),
            user=self.user
        )
        print(f"   OTP created: {otp.code}")

        response = self.api.post(self.url, {
            'identifier': self.phone,
            'otp': '123456',
            'purpose': 'LOGIN'
        }, format='json')

        print(f"   Status: {response.status_code}")
        print(f"   Has access token: {'access' in response.data}")

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        print("✅ Token received successfully")

    # ---------------------------------------------------------------
    def test_verify_otp_invalid_code(self):
        """تأیید OTP با کد اشتباه – باید ۴۰۰ برگرداند"""
        print("\n--- TEST: Verify OTP – Invalid Code ---")
        OTP.objects.create(
            identifier=self.phone,
            purpose='LOGIN',
            code='654321',
            expires_at=timezone.now() + timezone.timedelta(minutes=5),
            user=self.user
        )

        response = self.api.post(self.url, {
            'identifier': self.phone,
            'otp': '000000',
            'purpose': 'LOGIN'
        }, format='json')

        print(f"   Status: {response.status_code}")
        print(f"   Detail: {response.data.get('detail')}")

        self.assertEqual(response.status_code, 400)
        self.assertIn('نامعتبر', response.data.get('detail', ''))
        print("✅ Invalid code rejected")

    # ---------------------------------------------------------------
    def test_verify_otp_expired(self):
        """تأیید OTP منقضی‌شده – باید ۴۰۰ برگرداند"""
        print("\n--- TEST: Verify OTP – Expired ---")
        expired_otp = OTP.objects.create(
            identifier=self.phone,
            purpose='LOGIN',
            code='111222',
            expires_at=timezone.now() - timezone.timedelta(seconds=1),  # منقضی
            user=self.user
        )
        print(f"   OTP expired at: {expired_otp.expires_at}")

        response = self.api.post(self.url, {
            'identifier': self.phone,
            'otp': '111222',
            'purpose': 'LOGIN'
        }, format='json')

        print(f"   Status: {response.status_code}")
        print(f"   Detail: {response.data.get('detail')}")

        self.assertEqual(response.status_code, 400)
        print("✅ Expired OTP rejected")

    # ---------------------------------------------------------------
    def test_verify_otp_already_used(self):
        """تلاش برای استفاده مجدد از OTP – باید ۴۰۰ برگرداند"""
        print("\n--- TEST: Verify OTP – Already Used ---")
        otp = OTP.objects.create(
            identifier=self.phone,
            purpose='LOGIN',
            code='333444',
            expires_at=timezone.now() + timezone.timedelta(minutes=5),
            user=self.user,
            used=True,          # قبلاً استفاده شده
            used_at=timezone.now()
        )
        print(f"   OTP used at: {otp.used_at}")

        response = self.api.post(self.url, {
            'identifier': self.phone,
            'otp': '333444',
            'purpose': 'LOGIN'
        }, format='json')

        print(f"   Status: {response.status_code}")
        print(f"   Detail: {response.data.get('detail')}")

        self.assertEqual(response.status_code, 400)
        print("✅ Used OTP rejected")

    # ---------------------------------------------------------------
    def test_verify_otp_register_new_user(self):
        """تأیید OTP برای ثبت‌نام – باید کاربر جدید ساخته و توکن ۲۰۱ برگرداند"""
        print("\n--- TEST: Verify OTP – Register New User ---")
        new_phone = '09221112233'
        # OTP برای ثبت‌نام بدون user (کاربر هنوز وجود ندارد)
        otp = OTP.objects.create(
            identifier=new_phone,
            purpose='REGISTER',
            code='555666',
            expires_at=timezone.now() + timezone.timedelta(minutes=5),
            user=None            # کاربر هنوز ساخته نشده
        )
        print(f"   OTP created for new phone: {new_phone}")

        response = self.api.post(self.url, {
            'identifier': new_phone,
            'otp': '555666',
            'purpose': 'REGISTER'
        }, format='json')

        print(f"   Status: {response.status_code}")
        print(f"   Has access token: {'access' in response.data}")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(phone=new_phone).exists())
        self.assertIn('access', response.data)
        print("✅ New user registered & token received")