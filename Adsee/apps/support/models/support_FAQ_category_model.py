from django.db import models

class FAQCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام دسته")
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name="آیکون")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "دسته‌بندی سوالات"
        verbose_name_plural = "دسته‌بندی‌های سوالات"
        ordering = ['order']

    def __str__(self):
        return self.name
