from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, DriverProfile, ClientProfile, OTP


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
        self.assertEqual(profile.kyc_status, 'NOT_STARTED')
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