from django.db import models

class SupportContent(models.Model):
    class ContentType(models.TextChoices):
        CONTACT = 'CONTACT', 'تماس با ما'
        FAQ = 'FAQ', 'سوالات متداول'
        RULES = 'RULES', 'قوانین و مقررات شهری'  # جدید

    type = models.CharField(max_length=20, choices=ContentType.choices)
    title = models.CharField(max_length=200)
    body = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)
    image = models.ImageField(upload_to='support/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
