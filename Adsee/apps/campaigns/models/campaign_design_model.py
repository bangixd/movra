from django.db import models
from django.core.exceptions import ValidationError
from .campaign_model import Campaign
from .template_model import Template
from .banner_type_model import BannerType

class CampaignDesign(models.Model):
    class DesignType(models.TextChoices):
        USER_UPLOAD = "USER_UPLOAD", "User Upload"
        CUSTOM_DESIGN = "CUSTOM_DESIGN", "Custom Design"
        DEFAULT_TEMPLATE = "DEFAULT_TEMPLATE", "Default Template"

    class DesignStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In_Progress"
        COMPLETED = "COMPLETED", "Completed"
        REJECTED = "REJECTED", "Rejected"

    banner_type = models.ForeignKey(BannerType, on_delete=models.SET_NULL, null=True, blank=True)

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

