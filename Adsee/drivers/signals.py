from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DriverDocument

@receiver(post_save, sender=DriverDocument)
def update_driver_kyc_status(sender, instance, **kwargs):
    user = instance.user
    if not hasattr(user, 'driver_profile'):
        return

    profile = user.driver_profile
    docs = DriverDocument.objects.filter(user=user)

    if docs.filter(status=DriverDocument.ApprovalStatus.REJECTED).exists():
        profile.kyc_status = 'REJECTED'
    elif docs.count() > 0 and all(d.status == DriverDocument.ApprovalStatus.APPROVED for d in docs):
        profile.kyc_status = 'APPROVED'
    else:
        profile.kyc_status = 'PENDING'

    profile.save(update_fields=['kyc_status'])