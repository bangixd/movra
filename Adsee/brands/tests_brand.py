from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User, ClientProfile
from brands.models import Brand, BrandCategory
from geo.models import City
from campaigns.models import Campaign, CampaignSetting
from vehicles.models import VehicleType
from django.contrib.gis.geos import Point

class BrandManagementTest(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(user=self.client_user, full_name='C', national_id='1234567890')
        self.city = City.objects.create(name='تهران', center=Point(51.38, 35.68, srid=4326))
        self.category = BrandCategory.objects.create(name='فروشگاهی')
        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)

    def test_create_brand_pending(self):
        response = self.api.post('/api/brands/', {
            'name': 'برند جدید',
            'slug': 'new-brand',
            'city': self.city.id,
            'category': self.category.id,
            'phone': '09120000000',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        brand = Brand.objects.get(slug='new-brand')
        self.assertEqual(brand.status, 'PENDING')
        self.assertEqual(brand.client, self.client_profile)

    def test_list_brands_with_stats(self):
        Brand.objects.create(client=self.client_profile, name='B1', slug='b1', city=self.city, category=self.category, status='APPROVED')
        # ساخت کمپین فعال
        vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        campaign = Campaign.objects.create(client=self.client_profile, slogan='C1', brand_name=Brand.objects.get(slug='b1'), start_date=date.today(), status=Campaign.Status.ACTIVE)
        CampaignSetting.objects.create(campaign=campaign, active_days=5, activity_hours_per_day='08:00:00', max_driver=1, vehicle_type=vehicle_type)
        response = self.api.get('/api/brands/')
        self.assertEqual(response.status_code, 200)
        data = response.data[0]
        self.assertEqual(data['active_campaigns_count'], 1)
        self.assertGreaterEqual(data['remaining_days'], 0)

    def test_admin_review_brand(self):
        admin = User.objects.create_superuser(phone='09990000000', password='admin')
        self.api.force_authenticate(user=admin)
        brand = Brand.objects.create(client=self.client_profile, name='B2', slug='b2', city=self.city, category=self.category, status='PENDING')
        response = self.api.patch(f'/api/brands/{brand.id}/review/', {'status': 'APPROVED'}, format='json')
        self.assertEqual(response.status_code, 200)
        brand.refresh_from_db()
        self.assertEqual(brand.status, 'APPROVED')