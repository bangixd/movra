from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from clients.models import ClientProfile
from brands.models import Brand
from brands.services import BrandService

class BrandModelTest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(phone='09121112233', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='Client1', national_id='1234567890')
        self.other_client = User.objects.create_user(phone='09128889900', role=User.Role.CLIENT)
        self.other_profile = ClientProfile.objects.create(user=self.other_client, full_name='Client2', national_id='0987654321')

    def test_brand_belongs_to_client(self):
        brand = Brand.objects.create(client=self.client_profile, name='BrandA', slug='brand-a')
        self.assertEqual(brand.client, self.client_profile)

    def test_slug_unique(self):
        Brand.objects.create(client=self.client_profile, name='Test', slug='test')
        with self.assertRaises(Exception):
            Brand.objects.create(client=self.other_profile, name='Test2', slug='test')

class BrandAPITest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(phone='09121112233', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='Ali', national_id='1234567890')
        self.other_client = User.objects.create_user(phone='09121114455', role=User.Role.CLIENT)
        self.other_profile = ClientProfile.objects.create(user=self.other_client, full_name='Reza', national_id='1111111111')

        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)

    def test_create_brand(self):
        response = self.api.post('/v1/brands/', {'name': 'NewBrand', 'slug': 'new-brand'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Brand.objects.count(), 1)
        self.assertEqual(Brand.objects.first().client, self.client_profile)

    def test_list_only_own_brands(self):
        Brand.objects.create(client=self.client_profile, name='Mine', slug='mine')
        Brand.objects.create(client=self.other_profile, name='NotMine', slug='not-mine')
        response = self.api.get('/v1/brands/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Mine')

class BrandServiceTest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='Test')
        self.admin = User.objects.create_superuser(phone='09990000000', password='admin')

    def test_get_queryset_client(self):
        Brand.objects.create(client=self.client_profile, name='Brand 1', slug='b1')
        Brand.objects.create(client=self.client_profile, name='Brand 2', slug='b2', status='APPROVED')
        qs = BrandService.get_queryset(self.client_user)
        self.assertEqual(qs.count(), 2)

    def test_get_queryset_with_status_filter(self):
        Brand.objects.create(client=self.client_profile, name='Brand 1', slug='b1')
        Brand.objects.create(client=self.client_profile, name='Brand 2', slug='b2', status='APPROVED')
        qs = BrandService.get_queryset(self.client_user, 'APPROVED')
        self.assertEqual(qs.count(), 1)

    def test_review_brand_approved(self):
        brand = Brand.objects.create(client=self.client_profile, name='Test', slug='test')
        updated = BrandService.review_brand(brand, 'APPROVED')
        self.assertEqual(updated.status, 'APPROVED')

    def test_review_brand_invalid_status(self):
        brand = Brand.objects.create(client=self.client_profile, name='Test', slug='test2')
        with self.assertRaises(ValueError):
            BrandService.review_brand(brand, 'INVALID')