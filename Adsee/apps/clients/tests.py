from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from clients.models import ClientProfile

class ClientProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone='09121112233', role=User.Role.CLIENT)

    def test_create_real_client(self):
        profile = ClientProfile.objects.create(
            user=self.user,
            advertiser_type=ClientProfile.AdvertiserType.REAL,
            full_name='Sara Ahmadi',
            national_id='9876543210',
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.advertiser_type, ClientProfile.AdvertiserType.REAL)
        self.assertEqual(profile.kyc_status, 'PENDING')

    def test_create_legal_client(self):
        profile = ClientProfile.objects.create(
            user=self.user,
            advertiser_type=ClientProfile.AdvertiserType.LEGAL,
            company_name='Test Co.',
            national_economic_code='123456789012345',
            registration_number='12345',
        )
        self.assertEqual(profile.advertiser_type, ClientProfile.AdvertiserType.LEGAL)
        self.assertIsNone(profile.full_name)  # چون حقیقی نیست

    def test_string_representation_real(self):
        profile = ClientProfile.objects.create(
            user=self.user,
            advertiser_type=ClientProfile.AdvertiserType.REAL,
            full_name='Sara Ahmadi',
            national_id='1234567890',
        )
        self.assertIn('Sara Ahmadi', str(profile))

    def test_string_representation_legal(self):
        profile = ClientProfile.objects.create(
            user=self.user,
            advertiser_type=ClientProfile.AdvertiserType.LEGAL,
            company_name='Foo Ltd',
        )
        self.assertIn('Foo Ltd', str(profile))

    def test_is_advertising_active_default_false(self):
        profile = ClientProfile.objects.create(
            user=self.user,
            advertiser_type=ClientProfile.AdvertiserType.REAL,
            full_name='Sara',
            national_id='1234567890',
        )
        self.assertFalse(profile.is_advertising_active)