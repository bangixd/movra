from django.db import models
from django.contrib.gis.db import models as geomodels
from django.conf import settings


class Province(geomodels.Model):
    name = geomodels.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'استان'
        verbose_name_plural = 'استان‌ها'

    def __str__(self):
        return self.name


class City(geomodels.Model):
    province = geomodels.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cities'
    )
    name = geomodels.CharField(max_length=120)
    # مرکز تقریبی شهر
    center = geomodels.PointField(srid=4326, help_text="مختصات مرکز شهر")

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['province__name', 'name']

    def __str__(self):
        return self.name


class Neighborhood(geomodels.Model):
    city = geomodels.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='neighborhoods'
    )
    name = geomodels.CharField(max_length=150)
    # مرکز محله
    center = geomodels.PointField(srid=4326, help_text="مختصات مرکز محله")
    # شعاع تقریبی محله به متر (برای نمایش محدوده دایره‌ای)
    radius_meter = geomodels.PositiveIntegerField(default=2000)

    class Meta:
        ordering = ['city', 'name']

    def __str__(self):
        return f"{self.name}, {self.city.name}"


class SuggestedRoute(geomodels.Model):
    city = geomodels.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suggested_routes'
    )
    name = geomodels.CharField(max_length=200)
    description = geomodels.TextField(blank=True)
    # مسیر به‌صورت LineString ذخیره می‌شود
    path = geomodels.LineStringField(srid=4326, help_text="مسیر پیشنهادی")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"Route: {self.name}"


class DriverLocation(geomodels.Model):
    driver = geomodels.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='locations'
    )
    # توجه: این فیلد به مدل Trip در اپ campaign اشاره می‌کند.
    # اگر هنوز مدل Trip را نساخته‌اید، می‌توانید این خط را فعلاً کامنت کنید.
    trip = geomodels.ForeignKey(
        'trips.Trip',            # بعداً ساخته می‌شود
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locations'
    )
    point = geomodels.PointField(srid=4326)
    timestamp = geomodels.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            geomodels.Index(fields=['driver', '-timestamp']),
        ]

    def __str__(self):
        return f"Driver {self.driver_id} at {self.timestamp}"
