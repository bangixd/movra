from django.db import models
from .campaign_design_model import CampaignDesign

def product_image_upload_path(self, filename):
    return f'products/campaign_{self.campaign_design.campaign}/{filename}'

class ProductImage(models.Model):
    campaign_design = models.ForeignKey(CampaignDesign, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to=product_image_upload_path)

