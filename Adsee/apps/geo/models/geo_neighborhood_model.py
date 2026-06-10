from django.db import models
from django.contrib.gis.db import models as geomodels
from geo.models import City

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

