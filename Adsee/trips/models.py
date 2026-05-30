from django.db import models
from drivers.models import DriverProfile
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


class Trip(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACTIVE = 'ACTIVE', 'Active'
        PAUSED = 'PAUSED', 'Paused'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name='trips',
        null=True,
        blank=True,
    )
    campaign = models.ForeignKey(
        'campaigns.Campaign',
        on_delete=models.PROTECT,
        related_name='trips'
    )
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.PROTECT,
        related_name='trips',
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    # آمار نهایی (ممکن است بعداً توسط API خارجی پر شود)
    total_active_seconds = models.PositiveIntegerField(default=0, null=True ,blank=True)
    total_distance_km = models.FloatField(default=0.0, null=True ,blank=True)
    earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="درآمد محاسبه‌شده توسط سرویس خارجی",
        null=True,
        blank=True,
    )

    # اسنپ‌شات تنظیمات کمپین و خودرو در لحظه‌ی ایجاد
    snapshot = models.JSONField(default=dict, null=True, blank=True)

    #نصب بنر و تایید
    sticker_image = models.ImageField(upload_to='trips/installations/', null=True, blank=True)
    driver_car_image = models.ImageField(upload_to='trips/installations/', null=True, blank=True)
    installation_verified = models.BooleanField(default=False)
    installation_verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['driver'],
                condition=~models.Q(status__in=['COMPLETED', 'CANCELLED']),
                name='unique_active_trip_per_driver'
            )
        ]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['driver', '-created_at']),
        ]

    def clean(self):
        super().clean()
        # ۱. خودرو باید متعلق به راننده باشد
        if self.vehicle_id and self.driver_id:
            if self.vehicle.driver_id != self.driver_id:
                raise ValidationError("این خودرو متعلق به شما نیست.")

        # ۲. راننده فقط یک سفر فعال می‌تواند داشته باشد
        if self.status not in [self.Status.COMPLETED, self.Status.CANCELLED]:
            if Trip.objects.filter(
                driver=self.driver
            ).exclude(
                pk=self.pk
            ).exclude(
                status__in=[self.Status.COMPLETED, self.Status.CANCELLED]
            ).exists():
                raise ValidationError("شما یک سفر فعال دیگر دارید.")

        # ۳. کمپین نباید بیش از max_drivers راننده همزمان داشته باشد
        if self.status not in [self.Status.COMPLETED, self.Status.CANCELLED]:
            active_trips_count = Trip.objects.filter(
                campaign=self.campaign
            ).exclude(
                status__in=[self.Status.COMPLETED, self.Status.CANCELLED]
            ).exclude(pk=self.pk).count()
            if self.campaign.setting.max_driver and active_trips_count >= self.campaign.setting.max_driver:
                raise ValidationError("ظرفیت راننده‌های این کمپین تکمیل شده است.")

    def save(self, *args, **kwargs):

        if not kwargs.pop('skip_clean', False):
            self.full_clean()

        if self._state.adding:  # فقط هنگام ایجاد اولیه
            # اسنپ‌شات از اطلاعات ضروری
            self.snapshot = {
                'campaign': {
                    'id': self.campaign_id,
                    'title': self.campaign.slogan,
                    'start_date': str(self.campaign.start_date),
                    'end_date': str(self.campaign.end_date),
                },
                'vehicle': {
                    'id': self.vehicle_id,
                    'type': self.vehicle.vehicle_type.name,
                    'hourly_rate': str(self.vehicle.hourly_rate),
                    'plate': self.vehicle.plate_number,
                },
                'area_type': self.campaign.area.area_type if hasattr(self.campaign, 'area') else None,
            }
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Trip {self.id} - {self.driver} ({self.status})"

class TripAnalysis(models.Model):
    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name='analysis'
    )
    # زمان‌ها و مسافت
    active_seconds = models.PositiveIntegerField(default=0)
    distance_km = models.FloatField(default=0.0)
    # امتیاز دیده‌شدن و تخمین تعداد مشاهده
    exposure_score = models.FloatField(default=0.0)
    estimated_impressions = models.FloatField(default=0.0)
    # کیفیت داده و اطمینان
    data_quality = models.FloatField(default=0.0)
    confidence = models.FloatField(default=0.0)
    # ترافیک (میانگین نسبت ترافیک در طول سفر)
    avg_traffic_ratio = models.FloatField(default=0.0)
    # ذخیرهٔ کل پاسخ برای استفاده‌های بعدی
    raw_response = models.JSONField(default=dict, blank=True)
    # شناسهٔ analysis-run در سرویس Analytics (برای تسویه)
    analysis_run_id = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    #جزییات کسریات سفر
    night_factor = models.FloatField(default=1.0)
    long_stop_factor = models.FloatField(default=1.0)
    suspicious_stop_penalty = models.FloatField(default=0.0)
    invalid_data_penalty = models.FloatField(default=0.0)
    total_penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

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