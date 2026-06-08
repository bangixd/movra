from django.utils import timezone
from clients.models import ClientDocument, ClientProfile
from utils.update_client_kyc_status import update_kyc_status


class ClientDocumentService:
    """سرویس مدیریت مدارک کلاینت"""

    @staticmethod
    def get_queryset(user):
        """برگرداندن مدارک بر اساس نقش کاربر"""
        if not user.is_authenticated:
            return ClientDocument.objects.none()
        if user.is_staff:
            return ClientDocument.objects.all()
        return ClientDocument.objects.filter(user=user)

    @staticmethod
    def create_document(user, validated_data: dict) -> ClientDocument:
        """
        ایجاد مدرک جدید و به‌روزرسانی مرحلهٔ KYC
        """
        document = ClientDocument.objects.create(user=user, **validated_data)

        # به‌روزرسانی مرحلهٔ KYC
        profile = user.client_profile
        if profile.kyc_step == ClientProfile.KYCStep.UPLOAD_DOCUMENTS:
            profile.kyc_step = ClientProfile.KYCStep.VERIFICATION
            profile.save(update_fields=['kyc_step'])

        # به‌روزرسانی وضعیت کلی KYC
        update_kyc_status(user)

        return document

    @staticmethod
    def review_document(document, status: str, reject_reason: str = '') -> ClientDocument:
        """
        بررسی مدرک توسط ادمین (تأیید یا رد)
        Args:
            document: نمونهٔ مدرک
            status: APPROVED یا REJECTED
            reject_reason: دلیل رد (در صورت REJECTED)
        Returns:
            نمونهٔ به‌روزرسانی‌شده
        Raises:
            ValueError: اگر وضعیت نامعتبر باشد
        """
        valid_statuses = [ClientDocument.ApprovalStatus.APPROVED, ClientDocument.ApprovalStatus.REJECTED]
        if status not in valid_statuses:
            raise ValueError("وضعیت نامعتبر است")

        document.status = status
        document.reviewed_at = timezone.now()

        if status == ClientDocument.ApprovalStatus.REJECTED:
            document.reject_reason = reject_reason or ''

        document.save()

        # به‌روزرسانی وضعیت KYC پروفایل
        update_kyc_status(document.user)

        return document