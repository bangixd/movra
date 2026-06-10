from django.contrib.gis.db import models as geomodels

class Province(geomodels.Model):
    name = geomodels.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'استان'
        verbose_name_plural = 'استان‌ها'

    def __str__(self):
        return self.name

