from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Notification
from campaigns.models import Campaign, CampaignDesign

User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=Campaign)
def notify_drivers_new_campaign(sender, instance, created, **kwargs):
    # وقتی کمپین تازه ایجاد شود و فعال باشد، به همه راننده‌ها اطلاع بده
    if instance.status == Campaign.Status.ACTIVE:
        drivers = User.objects.filter(role=User.Role.DRIVER)
        for driver in drivers:
            Notification.objects.create(
                recipient=driver,
                notification_type=Notification.Type.NEW_CAMPAIGN,
                message=f'کمپین جدید: {instance.slogan}'
            )

@receiver(post_save, sender=CampaignDesign)
def notify_printshop_new_design(sender, instance, created, **kwargs):
    # وقتی یک چاپخانه به یک طرح اختصاص داده شود
    if instance.print_shop and instance.print_status == 'PENDING':
        # چک کن قبلاً برای همین طرح اعلان نفرستاده باشیم (با فیلتر)
        if not Notification.objects.filter(
            recipient=instance.print_shop.user,
            notification_type=Notification.Type.NEW_DESIGN,
            message__contains=str(instance.id)  # ساده‌سازی
        ).exists():
            Notification.objects.create(
                recipient=instance.print_shop.user,
                notification_type=Notification.Type.NEW_DESIGN,
                message=f'طرح جدید برای کمپین {instance.campaign.slogan} به شما واگذار شد.'
            )