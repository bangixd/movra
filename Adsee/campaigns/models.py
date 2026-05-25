from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.contrib.gis.db import models as geomodels
from django.core.exceptions import ValidationError


class Campaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT"
        WAITING_FOR_DESIGN = "WAITING_FOR_DESIGN"
        WAITING_FOR_PAYMENT = "WAITING_FOR_PAYMENT"
        ACTIVE = "ACTIVE"
        PAUSED = "PAUSED"
        COMPLETED = "COMPLETED"
        REJECTED = "REJECTED"

    client = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.CASCADE,
        related_name="campaigns"
    )

    slogan = models.CharField(max_length=255)
    brand_name = models.ForeignKey(
        'brands.Brand',
        on_delete=models.PROTECT,
        related_name='campaigns'
    )

    description = models.TextField(blank=True)

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.DRAFT)

    is_deleted = models.BooleanField(default=False)

    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.slogan} - {self.client_id}"

    def is_active_now(self):
        now = timezone.localtime()
        return (
            self.status == self.Status.ACTIVE
            and self.start_date <= now.date() <= self.end_date
        )


class CampaignSetting(models.Model):
    campaign = models.OneToOneField('Campaign', on_delete=models.CASCADE, related_name='setting')

    active_days = models.PositiveIntegerField()
    activity_hours_per_day = models.TimeField()

    max_driver = models.PositiveIntegerField()

    vehicle_type = models.ForeignKey(
        "vehicles.VehicleType",
        on_delete=models.PROTECT,
        related_name="campaigns"
    )


class Template(models.Model):
    name = models.CharField(max_length=100)
    variant = models.CharField(max_length=50, unique=True)
    preview_image = models.ImageField(upload_to='templates/', blank=True, null=True)

    def __str__(self):
        return self.name


class CampaignDesign(models.Model):
    class DesignType(models.TextChoices):
        USER_UPLOAD = "user_upload", "User Upload"
        CUSTOM_DESIGN = "custom_design", "Custom Design"
        DEFAULT_TEMPLATE = "default_template", "Default Template"

    class DesignStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In_Progress"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"

    campaign = models.OneToOneField(
        Campaign,
        on_delete=models.CASCADE,
        related_name="design"
    )

    design_type = models.CharField(
        max_length=30,
        choices=DesignType.choices
    )

    template = models.ForeignKey(
        Template,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaign_designs",
    )
    # فایل طرحی که کاربر آپلود می‌کند
    user_uploaded_file = models.FileField(upload_to="campaign/designs/user/", null=True, blank=True)

    # فایل نهایی طراحی شده توسط تیم
    final_design_file = models.FileField(upload_to="campaign/designs/final/", null=True, blank=True)

    logo_brand = models.FileField(upload_to="campaign/designs/logo_brand/", null=True, blank=True)

    designer_note = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=DesignStatus.choices,
        default=DesignStatus.PENDING
    )

    print_shop = models.ForeignKey(
        'print_shops.PrintShopProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_designs'
    )
    print_status = models.CharField(
        max_length=30,
        choices=[
            ('PENDING', 'Pending'),
            ('ACCEPTED', 'Accepted'),
            ('IN_PROGRESS', 'In Progress'),
            ('READY', 'Ready for Pickup'),
            ('DELIVERED', 'Delivered'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )
    estimated_ready_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.design_type == self.DesignType.DEFAULT_TEMPLATE and self.template is None:
            raise ValidationError({
                "template": "برای حالت Default Template انتخاب قالب الزامی است."
            })

        if self.design_type != self.DesignType.DEFAULT_TEMPLATE and self.template is not None:
            raise ValidationError({
                "template": "این فیلد فقط برای Default Template مجاز است."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.campaign.slogan} - {self.design_type}"


def product_image_upload_path(self, filename):
    return f'products/campaign_{self.campaign_design.campaign}/{filename}'


class ProductImage(models.Model):
    campaign_design = models.ForeignKey(CampaignDesign, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to=product_image_upload_path)


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


class CampaignCost(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        CONFIGURING = "CONFIGURING", "Configuring"
        READY_FOR_PAYMENT = "READY_FOR_PAYMENT", "Ready For Payment"
        PENDING_PAYMENT = "PENDING_PAYMENT", "Pending Payment"
        PAID = "PAID", "Paid"
        EXPIRED = "EXPIRED", "Expired"
        CANCELED = "CANCELED", "Canceled"

    campaign = models.OneToOneField(
        "Campaign",
        on_delete=models.CASCADE,
        related_name="cost"
    )

    # مرحله اجرا
    drivers_count = models.PositiveIntegerField(default=1)
    days_count = models.PositiveIntegerField(default=1)
    hours_per_day = models.PositiveIntegerField(default=1)
    vehicle_type = models.ForeignKey(
        "vehicles.VehicleType",
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    # انتخاب طراحی
    design_type = models.CharField(max_length=30, null=True, blank=True)

    # انتخاب محدوده
    area_type = models.CharField(max_length=30, null=True, blank=True)

    # جمع‌ها
    subtotal_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT
    )

    payment_expires_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_pending_payment(self, expire_minutes=30):
        self.status = self.Status.PENDING_PAYMENT
        self.payment_expires_at = timezone.now() + timedelta(minutes=expire_minutes)
        self.save(update_fields=["status", "payment_expires_at"])

    def mark_paid(self):
        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "paid_at"])

    def mark_expired(self):
        self.status = self.Status.EXPIRED
        self.save(update_fields=["status"])

    def is_expired(self):
        return (
            self.status == self.Status.PENDING_PAYMENT
            and self.payment_expires_at
            and timezone.now() > self.payment_expires_at
        )

    def __str__(self):
        return f"Cost for Campaign #{self.campaign_id}"


class CampaignCostItem(models.Model):
    class ItemType(models.TextChoices):
        EXECUTION = "EXECUTION", "Execution"
        DESIGN = "DESIGN", "Design"
        AREA = "AREA", "Area"
        DISCOUNT = "DISCOUNT", "Discount"
        TAX = "TAX", "Tax"

    campaign_cost = models.ForeignKey(
        CampaignCost,
        on_delete=models.CASCADE,
        related_name="items"
    )

    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    title = models.CharField(max_length=255)

    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    meta = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = (self.quantity or 0) * (self.unit_price or 0)
        super().save(*args, **kwargs)


class CampaignPricingRule(models.Model):
    class ValueType(models.TextChoices):
        DECIMAL = "DECIMAL", "Decimal"
        INTEGER = "INTEGER", "Integer"
        BOOLEAN = "BOOLEAN", "Boolean"
        TEXT = "TEXT", "Text"
        JSON = "JSON", "JSON"

    key = models.CharField(max_length=120, unique=True)
    title = models.CharField(max_length=255)
    value_type = models.CharField(max_length=20, choices=ValueType.choices, default=ValueType.DECIMAL)

    decimal_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    integer_value = models.IntegerField(null=True, blank=True)
    boolean_value = models.BooleanField(null=True, blank=True)
    text_value = models.CharField(max_length=500, null=True, blank=True)
    json_value = models.JSONField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    meta = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def value(self):
        if self.value_type == self.ValueType.DECIMAL:
            return self.decimal_value
        if self.value_type == self.ValueType.INTEGER:
            return self.integer_value
        if self.value_type == self.ValueType.BOOLEAN:
            return self.boolean_value
        if self.value_type == self.ValueType.TEXT:
            return self.text_value
        if self.value_type == self.ValueType.JSON:
            return self.json_value
        return None

    def set_value(self, value):
        self.decimal_value = None
        self.integer_value = None
        self.boolean_value = None
        self.text_value = None
        self.json_value = None

        if self.value_type == self.ValueType.DECIMAL:
            self.decimal_value = value
        elif self.value_type == self.ValueType.INTEGER:
            self.integer_value = value
        elif self.value_type == self.ValueType.BOOLEAN:
            self.boolean_value = value
        elif self.value_type == self.ValueType.TEXT:
            self.text_value = value
        elif self.value_type == self.ValueType.JSON:
            self.json_value = value


class CampaignInvoice(models.Model):

    class Status(models.TextChoices):
        ISSUED = "ISSUED", "Issued"
        PAID = "PAID", "Paid"
        EXPIRED = "EXPIRED", "Expired"
        VOID = "VOID", "Void"

    campaign = models.OneToOneField(
        "Campaign",
        on_delete=models.CASCADE,
        related_name="invoice"
    )

    campaign_cost = models.ForeignKey(
        CampaignCost,
        on_delete=models.PROTECT,
        related_name="invoices"
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices)

    subtotal_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)

    expires_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)

    snapshot = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)


class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        PENDING = 'PENDING', 'Pending'
        SUCCESSFUL = 'SUCCESSFUL', 'Successful'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    invoice = models.ForeignKey(CampaignInvoice, on_delete=models.PROTECT, related_name='transactions')
    authority = models.CharField(max_length=200, unique=True)  # شناسه یکتای زرین‌پال
    ref_id = models.CharField(max_length=200, blank=True, null=True)  # شماره پیگیری
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    response_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction {self.authority} - {self.status}"
