from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.gis.geos import Point, LineString
from accounts.models import User
from geo.models import Province, City, Neighborhood, SuggestedRoute, DriverLocation
from trips.models import Trip  # برای ارتباط DriverLocation با Trip


class GeoModelTest(TestCase):
    def setUp(self):
        self.province = Province.objects.create(name='Tehran')
        self.city = City.objects.create(province=self.province, name='Tehran City', center=Point(51.38, 35.68, srid=4326))
        self.neighborhood = Neighborhood.objects.create(city=self.city, name='Niavaran', center=Point(51.45, 35.80, srid=4326), radius_meter=2500)

    def test_city_creation(self):
        self.assertEqual(self.city.province, self.province)
        self.assertIsNotNone(self.city.center)

    def test_suggested_route_creation(self):
        line = LineString((51.0, 35.0), (51.1, 35.1), srid=4326)
        route = SuggestedRoute.objects.create(city=self.city, name='Route1', path=line)
        self.assertEqual(route.city, self.city)

class GeoAPITest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(phone='09991112233', password='adminpass')
        self.driver = User.objects.create_user(phone='09120000000', role=User.Role.DRIVER)
        self.api = APIClient()

    def test_non_admin_cannot_create_city(self):
        self.api.force_authenticate(user=self.driver)
        response = self.api.post('/v1/geo/cities/', {
            'name': 'Shiraz',
            'province': None,
            'center': 'POINT(51.38 35.68)'
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_city(self):
        self.api.force_authenticate(user=self.admin)
        province = Province.objects.create(name='Fars')
        response = self.api.post('/v1/geo/cities/', {
            'name': 'Shiraz',
            'province': province.id,
            'center': 'POINT(52.53 29.61)'
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_list_cities_authenticated(self):
        self.api.force_authenticate(user=self.driver)
        province = Province.objects.create(name='Esfahan')
        City.objects.create(name='Esfahan', province=province, center=Point(51.67, 32.65, srid=4326))
        response = self.api.get('/v1/geo/cities/')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)