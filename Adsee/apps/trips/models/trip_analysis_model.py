from django.db import models
from .trip_model import Trip


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
