from django.db import models

class AppDownloadLink(models.Model):
    class Platform(models.TextChoices):
        ANDROID = 'ANDROID', 'اندروید'
        IOS = 'IOS', 'iOS'
        PWA = 'PWA', 'وب اپلیکیشن'

    platform = models.CharField(max_length=20, choices=Platform.choices)
    version = models.CharField(max_length=20)
    url = models.URLField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "لینک دانلود"
        verbose_name_plural = "لینک‌های دانلود"
        unique_together = ('platform', 'version')

    def __str__(self):
        return f"{self.get_platform_display()} - v{self.version}"