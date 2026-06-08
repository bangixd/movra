from django.utils import timezone
from drivers.models import DriverDocument, DriverProfile


class DriverDocumentService:
    """سرویس مدیریت مدارک راننده"""

    @staticmethod
    def get_queryset(user):
        """
        برگرداندن مدارک بر اساس نقش کاربر.
        - ادمین: همهٔ مدارک
        - راننده: فقط مدارک خودش
        """
        if not user.is_authenticated:
            return DriverDocument.objects.none()
        if user.is_staff:
            return DriverDocument.objects.all()
        return DriverDocument.objects.filter(user=user)

    @staticmethod
    def create_document(user, serializer) -> DriverDocument:
        """
        ایجاد مدرک جدید و به‌روزرسانی مرحلهٔ ثبت‌نام.

        Args:
            user: کاربر جاری
            serializer: نمونهٔ Serializer معتبرشده
        """
        # Save the document via the serializer
        document = serializer.save(user=user)

        # Update the profile step
        profile = user.driver_profile
        if profile.registration_step == DriverProfile.RegistrationStep.DOCUMENTS:
            profile.registration_step = DriverProfile.RegistrationStep.VERIFICATION
            profile.kyc_submitted_at = timezone.now()
            profile.save(update_fields=['registration_step', 'kyc_submitted_at'])

        return document

    @staticmethod
    def review_document(document: DriverDocument, status: str, reject_reason: str = '') -> DriverDocument:
        """
        بررسی مدرک توسط ادمین (تأیید یا رد).
        Args:
            document: نمونهٔ مدرک
            status: APPROVED یا REJECTED
            reject_reason: دلیل رد (در صورت REJECTED)
        Returns:
            نمونهٔ به‌روزرسانی‌شده
        Raises:
            ValueError: اگر وضعیت نامعتبر باشد
        """
        valid_statuses = [DriverDocument.ApprovalStatus.APPROVED, DriverDocument.ApprovalStatus.REJECTED]
        if status not in valid_statuses:
            raise ValueError("وضعیت نامعتبر است")

        document.status = status
        document.reviewed_at = timezone.now()

        if status == DriverDocument.ApprovalStatus.REJECTED:
            document.reject_reason = reject_reason or ''

        document.save()

        # به‌روزرسانی وضعیت KYC پروفایل
        DriverDocumentService._update_kyc_status(document.user)

        return document

    @staticmethod
    def _update_kyc_status(user):
        """
        به‌روزرسانی وضعیت KYC پروفایل بر اساس وضعیت همهٔ مدارک.
        """
        profile = user.driver_profile
        docs = DriverDocument.objects.filter(user=user)

        if docs.filter(status=DriverDocument.ApprovalStatus.REJECTED).exists():
            profile.kyc_status = 'REJECTED'
        elif docs.exists() and all(d.status == DriverDocument.ApprovalStatus.APPROVED for d in docs):
            profile.kyc_status = 'APPROVED'
            if profile.registration_step == DriverProfile.RegistrationStep.VERIFICATION:
                profile.registration_step = DriverProfile.RegistrationStep.CONTRACT
        else:
            profile.kyc_status = 'PENDING'

        profile.kyc_reviewed_at = timezone.now()
        profile.save()