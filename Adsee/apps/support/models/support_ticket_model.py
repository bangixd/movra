from django.db import models
from django.conf import settings

class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'باز'
        CLOSED = 'CLOSED', 'بسته'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets',null=True,
    blank=True)
    subject = models.CharField(max_length=200, verbose_name="موضوع")
    name = models.CharField(max_length=100, verbose_name="نام و نام خانوادگی")
    phone = models.CharField(max_length=15, verbose_name="شماره تماس")
    message = models.TextField(verbose_name="پیام")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN, verbose_name="وضعیت")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تیکت پشتیبانی"
        verbose_name_plural = "تیکت‌های پشتیبانی"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.user.phone}"
