from django.db import models
from django.contrib.gis.db import models as geomodels
from geo.models import Province


class City(geomodels.Model):
    boundary = models.PolygonField(srid=4326, null=True, blank=True, help_text="محدودهٔ اداری شهر")
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

