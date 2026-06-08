from django.db import models
from .brand_category import BrandCategory

class Brand(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
    client = models.ForeignKey(
        'clients.ClientProfile',
        on_delete=models.CASCADE,
        related_name='brands'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, allow_unicode=True)
    logo = models.ImageField(upload_to='brands/logos/', blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    city = models.ForeignKey('geo.City', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(BrandCategory, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    telegram = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
