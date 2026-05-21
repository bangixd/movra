from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DriverDocument
from services.tasks import process_driver_document


@receiver(post_save, sender=DriverDocument)
def trigger_driver_document_processing(sender, instance, created, **kwargs):
    if created:
        # ارسال به Celery برای پردازش پس‌زمینه
        process_driver_document.delay(instance.id)