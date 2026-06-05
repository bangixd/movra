from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import DriverDocument, DriverProfile
from services.tasks import process_driver_document
import uuid



@receiver(post_save, sender=DriverDocument)
def trigger_driver_document_processing(sender, instance, created, **kwargs):
    if created:
        process_driver_document.delay(instance.id)


@receiver(pre_save, sender=DriverProfile)
def generate_referral_code(sender, instance, **kwargs):
    if not instance.referral_code:
        # یک کد یکتا ۸ کاراکتری (حروف و عدد) تولید کن
        instance.referral_code = uuid.uuid4().hex[:8].upper()