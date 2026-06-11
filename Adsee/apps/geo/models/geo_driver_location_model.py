from django.db import models
from django.contrib.gis.db import models as geomodels
from django.conf import settings

class DriverLocation(geomodels.Model):
    driver = geomodels.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='locations'
    )
    trip = geomodels.ForeignKey(
        'trips.Trip',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locations'
    )
    point = geomodels.PointField(srid=4326)
    timestamp = geomodels.DateTimeField(auto_now_add=True, db_index=True)

    source = models.CharField(
        max_length=10,
        choices=[('realtime', 'Real-time'), ('batch', 'Batch')],
        default='realtime',
        help_text="نحوه دریافت موقعیت"
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            geomodels.Index(fields=['driver', '-timestamp']),
            geomodels.Index(fields=['source']),
        ]

    def __str__(self):
        return f"Driver {self.driver_id} at {self.timestamp} ({self.source})"

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            geomodels.Index(fields=['driver', '-timestamp']),
        ]

    def __str__(self):
        return f"Driver {self.driver_id} at {self.timestamp}"
