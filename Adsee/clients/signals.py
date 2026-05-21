from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ClientDocument
from services.tasks import process_client_document

@receiver(post_save, sender=ClientDocument)
def trigger_client_document_processing(sender, instance, created, **kwargs):
    if created:
        process_client_document.delay(instance.id)