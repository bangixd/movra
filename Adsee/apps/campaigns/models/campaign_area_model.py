from django.db import models
from django.contrib.gis.db import models as geomodels
from django.core.exceptions import ValidationError
from .campaign_model import Campaign

class CampaignArea(geomodels.Model):
    class AreaType(models.TextChoices):
        CIRCLE = "CIRCLE", "Circle"
        SUGGESTED_ROUTE = "SUGGESTED_ROUTE", "Suggested Route"
        FREE_AREA = "FREE_AREA", "Free Area"

    campaign = geomodels.OneToOneField(
        Campaign,
        on_delete=models.CASCADE,
        related_name="area"
    )

    # نوع محدوده
    area_type = models.CharField(
        max_length=30,
        choices=AreaType.choices
    )

    # مرحله اول: انتخاب شهر
    city = geomodels.ForeignKey(
        "geo.City",
        on_delete=models.SET_NULL,
        related_name="campaign_areas",
        null=True,
        blank=True
    )

    # مرحله دوم: انتخاب محله
    neighborhood = geomodels.ForeignKey(
        "geo.Neighborhood",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaign_areas"
    )

    # حالت 1: دایره با شعاع قابل تغییر
    center_point = geomodels.PointField(null=True, blank=True)
    radius_meter = models.PositiveIntegerField(null=True, blank=True)

    # حالت 2: مسیرهای پیشنهادی
    suggested_route = geomodels.ForeignKey(
        "geo.SuggestedRoute",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaign_areas"
    )

    # حالت 3: منطقه آزاد
    region_polygon = geomodels.PolygonField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Area for {self.campaign_id} - {self.area_type}"

    def clean(self):

        if self.area_type == self.AreaType.CIRCLE:
            if not self.city or not self.neighborhood:
                raise ValidationError("برای حالت دایره، city و neighborhood الزامی است.")
            if not self.center_point or not self.radius_meter:
                raise ValidationError("برای حالت دایره، center_point و radius_meter الزامی است.")
            if self.suggested_route or self.region_polygon:
                raise ValidationError("برای حالت دایره فقط فیلدهای مربوطه باید پر شوند.")

        elif self.area_type == self.AreaType.SUGGESTED_ROUTE:
            if not self.city or not self.neighborhood:
                raise ValidationError("برای مسیر پیشنهادی، city و neighborhood الزامی است.")
            if not self.suggested_route:
                raise ValidationError("برای مسیر پیشنهادی، suggested_route الزامی است.")
            if self.center_point or self.radius_meter or self.region_polygon:
                raise ValidationError("برای مسیر پیشنهادی فقط فیلدهای مربوطه باید پر شوند.")

        elif self.area_type == self.AreaType.FREE_AREA:
            if not self.region_polygon or not self.city:
                raise ValidationError("برای منطقه آزاد، region_polygon الزامی است.")
            if self.neighborhood or self.center_point or self.radius_meter or self.suggested_route:
                raise ValidationError("برای منطقه آزاد فقط region_polygon باید پر شود.")
    # متدهایی برای محاسبه یا دسترسی راحت‌تر به داده‌ها
    def get_targeting_area_geometry(self):
        """
        خروجی:
        - در حالت CIRCLE => Polygon
        - در حالت SUGGESTED_ROUTE => هندسه route (مثلاً LineString/MultiLineString)
        - در حالت FREE_AREA => Polygon

        این متد برای کوئری‌های مکانی یا نمایش unified geometry مفید است.
        """
        if self.area_type == self.AreaType.FREE_AREA:
            return self.region_polygon

        if self.area_type == self.AreaType.SUGGESTED_ROUTE:
            if not self.suggested_route:
                return None
            return getattr(self.suggested_route, "path_geometry", None)

        if self.area_type == self.AreaType.CIRCLE:
            if not self.center_point or not self.radius_meter:
                return None

            # راه‌حل ساده و کاربردی:
            # buffer روی داده‌های جغرافیایی در 4326 از نظر متریک دقیق نیست.
            # در پروداکشن بهتر است به یک SRID متریک مثل 3857 یا UTM transform شود.
            point = self.center_point.clone()
            original_srid = point.srid

            try:
                # تبدیل موقت به Web Mercator برای بافر متری
                point.transform(3857)
                buffered = point.buffer(self.radius_meter)
                buffered.transform(original_srid)
                return buffered
            except Exception:
                return None

        return None

