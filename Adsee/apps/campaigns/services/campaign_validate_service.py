class CampaignValidationService:
    """سرویس اعتبارسنجی کمپین"""

    @staticmethod
    def ensure_required_steps_completed(campaign) -> None:
        """
        بررسی وجود مراحل ضروری کمپین (تنظیمات، طراحی، محدوده)
        Raises: ValueError در صورت عدم تکمیل
        """
        missing = []
        if not hasattr(campaign, 'setting'):
            missing.append('تنظیمات')
        if not hasattr(campaign, 'design'):
            missing.append('طراحی')
        if not hasattr(campaign, 'area'):
            missing.append('محدوده')

        if missing:
            raise ValueError(
                f"لطفاً مراحل زیر را تکمیل کنید: {', '.join(missing)}"
            )