from django.db import models

class Template(models.Model):
    name = models.CharField(max_length=100)
    variant = models.CharField(max_length=50, unique=True)
    preview_image = models.ImageField(upload_to='templates/', blank=True, null=True)

    def __str__(self):
        return self.name

