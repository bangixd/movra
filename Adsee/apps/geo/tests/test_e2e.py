from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.gis.geos import Point, LineString
from accounts.models import User
from drivers.models import DriverProfile
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import Campaign, CampaignSetting
from geo.models import Province, City, Neighborhood, SuggestedRoute, DriverLocation
from trips.models import Trip


class GeoE2ETest(TestCase):
    """
    تست جامع اپ Geo:
    - استان‌ها (CRUD + permissions)
    - شهرها (CRUD + permissions)
    - محله‌ها (CRUD + permissions)
    - مسیرهای پیشنهادی (CRUD + permissions)
    - موقعیت‌های راننده (real-time + batch + permissions)
    """

    def setUp(self):
        print("\n========== Geo E2E Test Setup ==========")

        # Users
        self.admin = User.objects.create_superuser(phone='09990000000', password='admin')
        self.driver_user = User.objects.create_user(phone='09120001122', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user,
            full_name='Test Driver',
            national_id='1234567890'
        )
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user,
            full_name='Test Client',
            national_id='9999999999'
        )

        # API Clients
        self.admin_api = APIClient()
        self.admin_api.force_authenticate(user=self.admin)

        self.driver_api = APIClient()
        self.driver_api.force_authenticate(user=self.driver_user)

        self.client_api = APIClient()
        self.client_api.force_authenticate(user=self.client_user)

        # Data for driver location tests
        self.vehicle_type = VehicleType.objects.create(name='Sedan', base_hourly_rate=50000)
        self.brand = Brand.objects.create(client=self.client_profile, name='Test Brand', slug='test-brand')
        self.campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='Test Campaign',
            brand_name=self.brand,
            start_date='2026-01-01',
            end_date='2026-01-10',
            status=Campaign.Status.ACTIVE
        )
        self.campaign_setting = CampaignSetting.objects.create(
            campaign=self.campaign,
            active_days=5,
            activity_hours_per_day='08:00:00',
            max_driver=2,
            vehicle_type=self.vehicle_type
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver_profile,
            vehicle_type=self.vehicle_type,
            plate_number='12A345B67',
            banner_max_width_cm=100,
            banner_max_height_cm=50
        )
        self.trip = Trip.objects.create(
            driver=self.driver_profile,
            campaign=self.campaign,
            vehicle=self.vehicle,
            status=Trip.Status.ACTIVE,
            start_time='2026-01-05T08:00:00Z'
        )

        print("✅ Setup complete")

    # ================================================================
    # PROVINCE TESTS
    # ================================================================
    def test_admin_can_create_province(self):
        """ادمین می‌تواند استان جدید بسازد"""
        print("\n--- TEST: Admin creates province ---")
        response = self.admin_api.post('/v1/geo/provinces/', {
            'name': 'Tehran'
        }, format='json')
        print(f"   Status: {response.status_code}, Data: {response.data}")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Province.objects.count(), 1)
        print("✅ Province created")

    def test_driver_cannot_create_province(self):
        """راننده نمی‌تواند استان جدید بسازد"""
        print("\n--- TEST: Driver cannot create province ---")
        response = self.driver_api.post('/v1/geo/provinces/', {
            'name': 'Fars'
        }, format='json')
        print(f"   Status: {response.status_code}")
        self.assertEqual(response.status_code, 403)
        print("✅ Driver blocked")

    def test_any_authenticated_user_can_list_provinces(self):
        """هر کاربر لاگین‌شده می‌تواند لیست استان‌ها را ببیند"""
        print("\n--- TEST: List provinces ---")
        Province.objects.create(name='Tehran')
        Province.objects.create(name='Esfahan')

        response = self.driver_api.get('/v1/geo/provinces/')
        print(f"   Status: {response.status_code}, Count: {len(response.data)}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        print("✅ Provinces listed")

    # ================================================================
    # CITY TESTS
    # ================================================================
    def test_admin_can_create_city(self):
        """ادمین می‌تواند شهر جدید بسازد"""
        print("\n--- TEST: Admin creates city ---")
        province = Province.objects.create(name='Tehran')

        response = self.admin_api.post('/v1/geo/cities/', {
            'name': 'Tehran City',
            'province': province.id,
            'center': 'POINT(51.38 35.68)'
        }, format='json')
        print(f"   Status: {response.status_code}, Data: {response.data}")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(City.objects.count(), 1)
        print("✅ City created")

    def test_list_cities_uses_list_serializer(self):
        """لیست شهرها از CityListSerializer استفاده می‌کند (خلاصه)"""
        print("\n--- TEST: List cities uses summary serializer ---")
        province = Province.objects.create(name='Tehran')
        City.objects.create(
            name='Tehran City',
            province=province,
            center=Point(51.38, 35.68, srid=4326)
        )

        response = self.driver_api.get('/v1/geo/cities/')
        print(f"   Status: {response.status_code}, Data: {response.data}")
        self.assertEqual(response.status_code, 200)
        # CityListSerializer باید province_name داشته باشد، center نداشته باشد
        self.assertIn('province_name', response.data[0])
        self.assertNotIn('center', response.data[0])
        print("✅ CityListSerializer used correctly")

    # ================================================================
    # NEIGHBORHOOD TESTS
    # ================================================================
    def test_admin_can_create_neighborhood(self):
        """ادمین می‌تواند محله جدید بسازد"""
        print("\n--- TEST: Admin creates neighborhood ---")
        province = Province.objects.create(name='Tehran')
        city = City.objects.create(
            name='Tehran City',
            province=province,
            center=Point(51.38, 35.68, srid=4326)
        )

        response = self.admin_api.post('/v1/geo/neighborhoods/', {
            'name': 'Niavaran',
            'city': city.id,
            'center': 'POINT(51.45 35.80)',
            'radius_meter': 2500
        }, format='json')
        print(f"   Status: {response.status_code}, Data: {response.data}")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Neighborhood.objects.count(), 1)
        print("✅ Neighborhood created")

    # ================================================================
    # SUGGESTED ROUTE TESTS
    # ================================================================
    def test_admin_can_create_route(self):
        """ادمین می‌تواند مسیر پیشنهادی جدید بسازد"""
        print("\n--- TEST: Admin creates suggested route ---")
        province = Province.objects.create(name='Tehran')
        city = City.objects.create(
            name='Tehran City',
            province=province,
            center=Point(51.38, 35.68, srid=4326)
        )

        response = self.admin_api.post('/v1/geo/routes/', {
            'name': 'Route 1',
            'city': city.id,
            'description': 'Main route',
            'path': 'LINESTRING(51.0 35.0, 51.1 35.1)'
        }, format='json')
        print(f"   Status: {response.status_code}, Data: {response.data}")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SuggestedRoute.objects.count(), 1)
        print("✅ Route created")

    def test_client_cannot_create_route(self):
        """کلاینت نمی‌تواند مسیر بسازد"""
        print("\n--- TEST: Client cannot create route ---")
        response = self.client_api.post('/v1/geo/routes/', {
            'name': 'Route X',
            'path': 'LINESTRING(51.0 35.0, 51.1 35.1)'
        }, format='json')
        print(f"   Status: {response.status_code}")
        self.assertEqual(response.status_code, 403)
        print("✅ Client blocked")

    # ================================================================
    # DRIVER LOCATION TESTS (Real-time)
    # ================================================================
    def test_driver_can_send_realtime_location(self):
        """راننده می‌تواند موقعیت لحظه‌ای ارسال کند"""
        print("\n--- TEST: Driver sends real-time location ---")
        response = self.driver_api.post('/v1/geo/driver-locations/', {
            'point': {'type': 'Point', 'coordinates': [51.39, 35.70]}
        }, format='json')
        print(f"   Status: {response.status_code}, Data: {response.data}")
        self.assertEqual(response.status_code, 201)
        loc = DriverLocation.objects.first()
        self.assertEqual(loc.source, 'realtime')
        self.assertEqual(loc.driver, self.driver_user)
        print("✅ Real-time location saved with source='realtime'")

    def test_non_driver_cannot_send_location(self):
        """کلاینت نمی‌تواند موقعیت ارسال کند"""
        print("\n--- TEST: Client cannot send location ---")
        response = self.client_api.post('/v1/geo/driver-locations/', {
            'point': {'type': 'Point', 'coordinates': [51.39, 35.70]}
        }, format='json')
        print(f"   Status: {response.status_code}")
        self.assertEqual(response.status_code, 403)
        print("✅ Client blocked")

    # ================================================================
    # DRIVER LOCATION TESTS (Batch)
    # ================================================================
    def test_driver_can_send_batch_locations(self):
        """راننده می‌تواند موقعیت‌های دسته‌ای ارسال کند"""
        print("\n--- TEST: Driver sends batch locations ---")
        response = self.driver_api.post('/v1/geo/driver-locations/batch/', {
            'trip_id': self.trip.id,
            'points': [
                {'lat': 35.70, 'lon': 51.39, 'timestamp': 1715172000},
                {'lat': 35.71, 'lon': 51.40, 'timestamp': 1715172060},
            ]
        }, format='json')
        print(f"   Status: {response.status_code}, Data: {response.data}")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(DriverLocation.objects.count(), 2)
        for loc in DriverLocation.objects.all():
            self.assertEqual(loc.source, 'batch')
        print("✅ Batch locations saved with source='batch'")

    def test_batch_requires_active_trip(self):
        """Batch فقط برای سفرهای فعال مجاز است"""
        print("\n--- TEST: Batch requires active trip ---")
        self.trip.status = Trip.Status.COMPLETED
        self.trip.save()

        response = self.driver_api.post('/v1/geo/driver-locations/batch/', {
            'trip_id': self.trip.id,
            'points': [{'lat': 35.70, 'lon': 51.39, 'timestamp': 1715172000}]
        }, format='json')
        print(f"   Status: {response.status_code}, Data: {response.data}")
        self.assertEqual(response.status_code, 400)
        self.assertIn('سفر فعال نیست', response.data.get('error', ''))
        print("✅ Non-active trip rejected")

    # ================================================================
    # PERMISSION TESTS (Admin access)
    # ================================================================
    def test_admin_can_see_all_locations(self):
        """ادمین می‌تواند همهٔ موقعیت‌ها را ببیند"""
        print("\n--- TEST: Admin sees all locations ---")
        # Create locations for driver
        DriverLocation.objects.create(
            driver=self.driver_user,
            trip=self.trip,
            point=Point(51.39, 35.70, srid=4326)
        )
        # Create another driver
        other_driver = User.objects.create_user(phone='09220000000', role=User.Role.DRIVER)
        DriverProfile.objects.create(user=other_driver, full_name='Other', national_id='8888888888')
        DriverLocation.objects.create(
            driver=other_driver,
            point=Point(51.40, 35.71, srid=4326)
        )

        response = self.admin_api.get('/v1/geo/driver-locations/')
        print(f"   Status: {response.status_code}, Count: {len(response.data)}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        print("✅ Admin sees all locations")

    def test_driver_only_sees_own_locations(self):
        """راننده فقط موقعیت‌های خودش را می‌بیند"""
        print("\n--- TEST: Driver sees only own locations ---")
        DriverLocation.objects.create(
            driver=self.driver_user,
            point=Point(51.39, 35.70, srid=4326)
        )
        other_driver = User.objects.create_user(phone='09220000000', role=User.Role.DRIVER)
        DriverProfile.objects.create(user=other_driver, full_name='Other', national_id='8888888888')
        DriverLocation.objects.create(
            driver=other_driver,
            point=Point(51.40, 35.71, srid=4326)
        )

        response = self.driver_api.get('/v1/geo/driver-locations/')
        print(f"   Status: {response.status_code}, Count: {len(response.data)}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        print("✅ Driver sees only own locations")