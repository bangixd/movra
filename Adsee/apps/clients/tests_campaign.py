from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.gis.geos import Point, Polygon

from accounts.models import User
from drivers.models import DriverProfile
from clients.models import ClientProfile
from brands.models import Brand
from vehicles.models import VehicleType, Vehicle
from campaigns.models import (
    Campaign, CampaignSetting, CampaignDesign, CampaignArea,
    CampaignGoal, BannerType, Template
)
from geo.models import City
from trips.models import Trip, TripAnalysis
from print_shops.models import PrintShopProfile


class ClientCampaignListTest(TestCase):
    def setUp(self):
        print("\n" + "=" * 60)
        print("   🚀 شروع تست لیست کمپین‌های کلاینت")
        print("=" * 60)

        # ---------- کلاینت ----------
        self.client_user = User.objects.create_user(phone='09121111111', role=User.Role.CLIENT)
        self.client_profile = ClientProfile.objects.create(
            user=self.client_user,
            full_name='Client Sara',
            national_id='1234567890'
        )
        print("✅ کلاینت ساخته شد")

        # ---------- برند ----------
        self.brand = Brand.objects.create(
            client=self.client_profile,
            name='Brand Test',
            slug='brand-test'
        )
        print("✅ برند ساخته شد")

        # ---------- نوع خودرو ----------
        self.vehicle_type = VehicleType.objects.create(
            name='Sedan',
            base_hourly_rate=50000
        )
        print("✅ نوع خودرو ساخته شد")

        # ---------- هدف و نوع بنر ----------
        self.goal = CampaignGoal.objects.create(name='افزایش فروش', is_active=True)
        self.banner_type = BannerType.objects.create(name='استیکر روی درها', is_active=True)
        template = Template.objects.create(name='Test Template', variant='test-1')
        print("✅ هدف و نوع بنر ساخته شد")

        # ---------- شهر ----------
        self.city = City.objects.create(
            name='تهران',
            center=Point(51.38, 35.68, srid=4326)
        )
        print("✅ شهر ساخته شد")

        # ---------- چاپخانه ----------
        self.print_shop_user = User.objects.create_user(phone='09123334455', role=User.Role.PRINT_SHOP)
        self.print_shop = PrintShopProfile.objects.create(
            user=self.print_shop_user,
            shop_name='چاپخانه تست',
            address='تهران، خیابان ولیعصر',
            phone='02112345678'
        )
        print("✅ چاپخانه ساخته شد")

        # ---------- کمپین فعال (با راننده) ----------
        self.active_campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='کمپین فعال',
            brand_name=self.brand,
            goal=self.goal,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
            status=Campaign.Status.ACTIVE
        )
        CampaignSetting.objects.create(
            campaign=self.active_campaign,
            active_days=5,
            activity_hours_per_day='08:00:00',
            max_driver=2,
            vehicle_type=self.vehicle_type
        )
        self.active_design = CampaignDesign.objects.create(
            campaign=self.active_campaign,
            design_type=CampaignDesign.DesignType.DEFAULT_TEMPLATE,
            banner_type=self.banner_type,
            print_shop=self.print_shop,
            template=template,
            status=CampaignDesign.DesignStatus.COMPLETED
        )
        # CampaignArea.objects.create(
        #     campaign=self.active_campaign,
        #     area_type=CampaignArea.AreaType.CIRCLE,
        #     city=self.city,
        #     center_point=Point(51.38, 35.68, srid=4326),
        #     radius_meter=5000
        # )
        polygon = Polygon(((51.0, 35.0), (51.0, 36.0), (52.0, 36.0), (52.0, 35.0), (51.0, 35.0)), srid=4326)
        self.area = CampaignArea.objects.create(
            campaign=self.active_campaign,
            area_type=CampaignArea.AreaType.FREE_AREA,
            city=self.city,
            region_polygon=polygon
        )
        # راننده برای کمپین فعال
        self.driver_user = User.objects.create_user(phone='09122222222', role=User.Role.DRIVER)
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver_user,
            full_name='Ali Rezaei',
            national_id='1234567890',
            birth_date='1990-01-01',
            registration_step=4,
            is_contract_accepted=True
        )
        self.vehicle = Vehicle.objects.create(
            driver=self.driver_profile,
            vehicle_type=self.vehicle_type,
            plate_number='12A345B67',
            vehicle_model='پژو 206',
            banner_max_width_cm=100,
            banner_max_height_cm=50
        )
        self.active_trip = Trip.objects.create(
            driver=self.driver_profile,
            campaign=self.active_campaign,
            vehicle=self.vehicle,
            status=Trip.Status.ACTIVE,
            start_time=timezone.now() - timedelta(hours=2),
            sticker_image='trips/installations/sticker.jpg',
            driver_car_image='trips/installations/driver.jpg'
        )
        TripAnalysis.objects.create(
            trip=self.active_trip,
            active_seconds=7200,
            distance_km=15.5,
            estimated_impressions=1200
        )
        print("✅ کمپین فعال با راننده ساخته شد")

        # ---------- کمپین تکمیل‌شده ----------
        self.completed_campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='کمپین تکمیل‌شده',
            brand_name=self.brand,
            goal=self.goal,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=5),
            status=Campaign.Status.COMPLETED
        )
        CampaignSetting.objects.create(
            campaign=self.completed_campaign,
            active_days=3,
            activity_hours_per_day='06:00:00',
            max_driver=1,
            vehicle_type=self.vehicle_type
        )
        CampaignDesign.objects.create(
            campaign=self.completed_campaign,
            design_type=CampaignDesign.DesignType.USER_UPLOAD,
            banner_type=self.banner_type,
            print_shop=self.print_shop,
            status=CampaignDesign.DesignStatus.COMPLETED
        )
        print("✅ کمپین تکمیل‌شده ساخته شد")

        # ---------- کمپین لغوشده ----------
        self.cancelled_campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='کمپین لغوشده',
            brand_name=self.brand,
            goal=self.goal,
            start_date=date.today() - timedelta(days=2),
            status=Campaign.Status.REJECTED
        )
        print("✅ کمپین لغوشده ساخته شد")

        # ---------- کمپین در انتظار (DRAFT) ----------
        self.draft_campaign = Campaign.objects.create(
            client=self.client_profile,
            slogan='کمپین پیش‌نویس',
            brand_name=self.brand,
            goal=self.goal,
            start_date=date.today(),
            status=Campaign.Status.DRAFT
        )
        print("✅ کمپین پیش‌نویس ساخته شد")

        # ---------- API Client ----------
        self.api = APIClient()
        self.api.force_authenticate(user=self.client_user)
        print("✅ احراز هویت انجام شد")
        print("-" * 60)

    # ==============================
    # تست ۱: لیست همهٔ کمپین‌ها
    # ==============================
    def test_01_list_all_campaigns(self):
        print("\n📋 تست ۱: لیست همهٔ کمپین‌ها")
        response = self.api.get('/api/clients/campaigns/')
        print(f"   Status: {response.status_code}")
        print(f"   Count: {len(response.data)}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)  # هر چهار کمپین
        print("✅ همهٔ کمپین‌ها برگشت داده شدند")

    # ==============================
    # تست ۲: فیلتر کمپین‌های فعال
    # ==============================
    def test_02_filter_active_campaigns(self):
        print("\n🔍 تست ۲: فیلتر کمپین‌های فعال")
        response = self.api.get('/api/clients/campaigns/?status=active')
        print(f"   Status: {response.status_code}")
        print(f"   Count: {len(response.data)}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['slogan'], 'کمپین فعال')
        print("✅ فقط کمپین فعال برگشت داده شد")

    # ==============================
    # تست ۳: فیلتر کمپین‌های تکمیل‌شده
    # ==============================
    def test_03_filter_completed_campaigns(self):
        print("\n🔍 تست ۳: فیلتر کمپین‌های تکمیل‌شده")
        response = self.api.get('/api/clients/campaigns/?status=completed')
        print(f"   Status: {response.status_code}")
        print(f"   Count: {len(response.data)}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['slogan'], 'کمپین تکمیل‌شده')
        print("✅ فقط کمپین تکمیل‌شده برگشت داده شد")

    # ==============================
    # تست ۴: فیلتر کمپین‌های در انتظار
    # ==============================
    def test_04_filter_pending_campaigns(self):
        print("\n🔍 تست ۴: فیلتر کمپین‌های در انتظار")
        response = self.api.get('/api/clients/campaigns/?status=pending')
        print(f"   Status: {response.status_code}")
        print(f"   Count: {len(response.data)}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['slogan'], 'کمپین پیش‌نویس')
        print("✅ فقط کمپین پیش‌نویس برگشت داده شد")

    # ==============================
    # تست ۵: فیلتر کمپین‌های لغوشده
    # ==============================
    def test_05_filter_cancelled_campaigns(self):
        print("\n🔍 تست ۵: فیلتر کمپین‌های لغوشده")
        response = self.api.get('/api/clients/campaigns/?status=cancelled')
        print(f"   Status: {response.status_code}")
        print(f"   Count: {len(response.data)}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['slogan'], 'کمپین لغوشده')
        print("✅ فقط کمپین لغوشده برگشت داده شد")

    # ==============================
    # تست ۶: بررسی جزئیات کمپین فعال
    # ==============================
    def test_06_active_campaign_details(self):
        print("\n📊 تست ۶: جزئیات کمپین فعال با رانندگان")
        response = self.api.get('/api/clients/campaigns/?status=active')
        print(f"   Status: {response.status_code}")

        self.assertEqual(response.status_code, 200)
        campaign = response.data[0]

        # بررسی فیلدهای اصلی
        self.assertEqual(campaign['brand_name'], 'Brand Test')
        self.assertIsNotNone(campaign['region'])
        self.assertEqual(campaign['status'], 'ACTIVE')
        self.assertEqual(campaign['banner_type'], 'استیکر روی درها')
        self.assertIsNotNone(campaign['print_shop_name'])
        self.assertIsNotNone(campaign['print_shop_address'])
        print(f"   برند: {campaign['brand_name']}")
        print(f"   منطقه: {campaign['region']}")
        print(f"   چاپخانه: {campaign['print_shop_name']}")

        # بررسی رانندگان فعال
        active_drivers = campaign['active_drivers']
        self.assertGreater(len(active_drivers), 0)
        driver = active_drivers[0]
        self.assertEqual(driver['driver_name'], 'Ali Rezaei')
        self.assertEqual(driver['trip_status'], 'ACTIVE')
        print(f"   راننده: {driver['driver_name']}")
        print(f"   وضعیت سفر: {driver['trip_status']}")
        print("✅ جزئیات کمپین و راننده درست است")

    # ==============================
    # تست ۷: عدم دسترسی کلاینت دیگر
    # ==============================
    def test_07_other_client_cannot_see(self):
        print("\n🔒 تست ۷: کلاینت دیگر نمی‌تواند کمپین‌ها را ببیند")
        other_user = User.objects.create_user(phone='09120000000', role=User.Role.CLIENT)
        ClientProfile.objects.create(user=other_user, full_name='Other', national_id='1111111111')
        self.api.force_authenticate(user=other_user)
        response = self.api.get('/api/clients/campaigns/')
        print(f"   Status: {response.status_code}")
        print(f"   Count: {len(response.data)}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)  # هیچ کمپینی برای این کلاینت نیست
        print("✅ کلاینت دیگر فقط کمپین‌های خودش را می‌بیند")

    def tearDown(self):
        print("\n" + "=" * 60)
        print("   🏁 پایان تست لیست کمپین‌های کلاینت")
        print("=" * 60 + "\n")