from django.db import models
from django.conf import settings

class ClientDocument(models.Model):
    class DocumentType(models.TextChoices):
        # مدارک حقیقی
        NATIONAL_ID_FRONT = 'NATIONAL_ID_FRONT', 'روی کارت ملی'
        NATIONAL_ID_BACK = 'NATIONAL_ID_BACK', 'پشت کارت ملی'
        SELFIE = 'SELFIE', 'عکس سلفی'
        # مدارک حقوقی
        BUSINESS_LICENSE = 'BUSINESS_LICENSE', 'گواهی کسب'
        ECONOMIC_CODE = 'ECONOMIC_CODE', 'کد اقتصادی'
        # سایر
        OTHER = 'OTHER', 'سایر'

    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_documents')
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file = models.FileField(upload_to='clients/documents/')
    status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.TextField(blank=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.phone} - {self.document_type}"