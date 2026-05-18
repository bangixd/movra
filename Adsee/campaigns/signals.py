from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CampaignSetting
from django.utils import timezone

@receiver(post_save, sender=CampaignSetting)
def update_campaign_end_date(sender, instance, created, **kwargs):
    campaign = instance.campaign
    if campaign.start_date and instance.active_days:
        campaign.end_date = campaign.start_date + timezone.timedelta(days=instance.active_days)
        campaign.save(update_fields=['end_date'])