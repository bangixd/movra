from django.conf import settings
from django.contrib.gis.db import models

class PrintShopProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='print_shop_profile'
    )
    shop_name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    location = models.PointField(srid=4326, null=True, blank=True)  # موقعیت روی نقشه
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_name