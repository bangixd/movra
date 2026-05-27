from django.db import models

class SupportContent(models.Model):
    class ContentType(models.TextChoices):
        CONTACT = 'CONTACT', 'تماس با ما'
        ABOUT = 'ABOUT', 'درباره ما'
        FAQ = 'FAQ', 'سوالات متداول'

    type = models.CharField(max_length=20, choices=ContentType.choices)
    title = models.CharField(max_length=200)
    body = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title