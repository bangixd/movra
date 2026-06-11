from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .trip_model import Trip


class HourlyActivity(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='hourly_activities'
    )
    hour = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="ساعت شبانه‌روز (0 تا 23)"
    )
    active_seconds = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('trip', 'hour')
        verbose_name = "فعالیت ساعتی"
        verbose_name_plural = "فعالیت‌های ساعتی"

    def __str__(self):
        return f"Trip {self.trip_id} - Hour {self.hour}: {self.active_seconds}s"