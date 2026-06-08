from django.db import models
from .campaign_area_model import CampaignArea
from .campaign_design_model import CampaignDesign
from .banner_type_model import BannerType

class CampaignPackage(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    vehicle_type = models.ForeignKey('vehicles.VehicleType', on_delete=models.PROTECT)
    active_days = models.PositiveIntegerField()
    hours_per_day = models.PositiveIntegerField()  # یا TimeField
    max_driver = models.PositiveIntegerField()
    banner_type = models.ForeignKey(BannerType, on_delete=models.PROTECT, null=True, blank=True)
    design_type = models.CharField(max_length=30, choices=CampaignDesign.DesignType.choices, default='DEFAULT_TEMPLATE')
    area_type = models.CharField(max_length=30, choices=CampaignArea.AreaType.choices, default='CIRCLE')
    price = models.DecimalField(max_digits=12, decimal_places=2)  # قیمت کل پکیج
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
