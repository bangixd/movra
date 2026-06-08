from django.db import models

class CampaignPricingRule(models.Model):
    """
    DESIGN_BASE_COST

    DESIGN_CUSTOM_COST

    DESIGN_UPLOAD_COST

    AREA_CIRCLE_COST_PER_KM

    AREA_SUGGESTED_ROUTE_COST_PER_KM

    AREA_FREE_COST_MULTIPLIER

    DRIVER_COST_PER_DAY

    BILLBOARD_DAILY_IMPRESSIONS
    اینها کلید های اجباری و پایه هستند که ادمین باید انها را مقدار دهی کند
    """
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

