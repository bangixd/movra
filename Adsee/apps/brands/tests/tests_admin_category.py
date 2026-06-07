from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from brands.models import BrandCategory

class AdminBrandCategoryTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(phone='09990000000', password='admin')
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_create_category(self):
        response = self.client.post('/v1/brands/admin/categories/', {
            'name': 'فروشگاهی',
            'is_active': True
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(BrandCategory.objects.filter(name='فروشگاهی').exists())

    def test_list_categories(self):
        BrandCategory.objects.create(name='خدماتی', is_active=True)
        BrandCategory.objects.create(name='فروشگاهی', is_active=False)
        response = self.client.get('/v1/brands/admin/categories/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_update_category(self):
        cat = BrandCategory.objects.create(name='قدیمی', is_active=True)
        response = self.client.patch(f'/v1/brands/admin/categories/{cat.id}/', {
            'name': 'جدید',
            'is_active': False
        }, format='json')
        self.assertEqual(response.status_code, 200)
        cat.refresh_from_db()
        self.assertEqual(cat.name, 'جدید')
        self.assertFalse(cat.is_active)

    def test_delete_category(self):
        cat = BrandCategory.objects.create(name='حذفی', is_active=True)
        response = self.client.delete(f'/v1/brands/admin/categories/{cat.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(BrandCategory.objects.filter(id=cat.id).exists())

    def test_non_admin_cannot_create(self):
        user = User.objects.create_user(phone='09120000000', role=User.Role.CLIENT)
        self.client.force_authenticate(user=user)
        response = self.client.post('/v1/brands/admin/categories/', {
            'name': 'غیرمجاز'
        }, format='json')
        self.assertEqual(response.status_code, 403)