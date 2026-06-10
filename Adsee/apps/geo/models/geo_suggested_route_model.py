from django.db import models
from django.contrib.gis.db import models as geomodels
from geo.models import City

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

