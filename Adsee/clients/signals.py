from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ClientDocument

@receiver(post_save, sender=ClientDocument)
def update_client_kyc_status(sender, instance, **kwargs):
    user = instance.user
    if not hasattr(user, 'client_profile'):
        return

    profile = user.client_profile
    docs = ClientDocument.objects.filter(user=user)

    if docs.filter(status=ClientDocument.ApprovalStatus.REJECTED).exists():
        profile.kyc_status = 'REJECTED'
    elif docs.count() > 0 and all(d.status == ClientDocument.ApprovalStatus.APPROVED for d in docs):
        profile.kyc_status = 'APPROVED'
    else:
        profile.kyc_status = 'PENDING'

    profile.save(update_fields=['kyc_status'])