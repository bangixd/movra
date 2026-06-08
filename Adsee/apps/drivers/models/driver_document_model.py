from django.db import models
from django.conf import settings

class DriverDocument(models.Model):
    class DocumentType(models.TextChoices):
        PROFILE_PICTURE = 'PROFILE_PICTURE', 'عکس پروفایل'
        DRIVING_LICENSE = 'DRIVING_LICENSE', 'گواهینامه'
        VEHICLE_CARD = 'VEHICLE_CARD', 'کارت خودرو'
        GREEN_SHEET = 'GREEN_SHEET', 'برگه سبز'

    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار'
        APPROVED = 'APPROVED', 'تأیید شده'
        REJECTED = 'REJECTED', 'رد شده'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='driver_documents')
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file = models.FileField(upload_to='drivers/documents/')
    status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.phone} - {self.document_type}"