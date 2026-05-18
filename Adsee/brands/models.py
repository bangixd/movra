from django.db import models


class Brand(models.Model):
    client = models.ForeignKey(
        'accounts.ClientProfile',
        on_delete=models.CASCADE,
        related_name='brands'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, allow_unicode=True)
    logo = models.ImageField(upload_to='brands/logos/', blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name