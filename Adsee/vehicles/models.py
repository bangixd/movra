from django.db import models
from decimal import Decimal
from drivers.models import DriverProfile


class VehicleType(models.Model):
    name = models.CharField(max_length=50, unique=True)          # Sedan, SUV, ...
    description = models.TextField(blank=True)
    # قیمت پایه ساعتی (قابل تغییر توسط ادمین)
    base_hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('50_000'),
        help_text="نرخ ساعتی پایه (تومان)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "نوع خودرو"
        verbose_name_plural = "انواع خودرو"
        ordering = ['name']

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )
    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.PROTECT,     # اگر نوع خودرو حذف شود، خودروها بی‌صاحب نشوند
        related_name='vehicles'
    )

    # مشخصات ظاهری
    vehicle_model = models.CharField(max_length=100, blank=True)
    vehicle_year = models.CharField(max_length=4, blank=True)
    vehicle_color = models.CharField(max_length=50, blank=True)

    # مدارک
    plate_number = models.CharField(max_length=20, unique=True, help_text="شماره پلاک")
    plate_image = models.ImageField(upload_to="vehicles/plates/", blank=True)
    license_number = models.CharField(max_length=20, blank=True, help_text="شماره گواهینامه یا برگه ثبت خودرو")

    # ابعاد بنر قابل نصب روی این خودرو
    banner_max_width_cm = models.PositiveIntegerField()
    banner_max_height_cm = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plate_number} ({self.vehicle_type.name})"

    @property
    def hourly_rate(self):
        """نرخ ساعتی خودرو = نرخ پایه نوع خودرو"""
        return self.vehicle_type.base_hourly_rate