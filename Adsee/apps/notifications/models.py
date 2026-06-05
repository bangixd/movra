from django.db import models
from django.conf import settings

class Notification(models.Model):
    class Type(models.TextChoices):
        NEW_CAMPAIGN = 'NEW_CAMPAIGN', 'New Campaign'
        NEW_DESIGN = 'NEW_DESIGN', 'New Design Assigned'
        # ... انواع دیگر

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=Type.choices)
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message[:50]