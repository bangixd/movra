from campaigns.models import CampaignSetting

class CampaignSettingService:
    """سرویس مدیریت تنظیمات کمپین"""

    @staticmethod
    def get_queryset(user):
        """
        برگرداندن تنظیمات کمپین‌های کاربر
        - ادمین: همهٔ تنظیمات
        - کلاینت: فقط تنظیمات کمپین‌های خودش
        """
        if not user.is_authenticated:
            return CampaignSetting.objects.none()
        if user.is_staff:
            return CampaignSetting.objects.all()
        return CampaignSetting.objects.filter(campaign__client__user=user)

    @staticmethod
    def get_client_campaign(user):
        """
        یافتن کمپین کلاینت (برای ایجاد/ویرایش تنظیمات)
        توجه: هر کلاینت ممکن است چند کمپین داشته باشد.
        این متد کمپین مورد نظر را بر اساس داده‌های درخواست پیدا می‌کند.
        """
        from campaigns.models import Campaign
        # این متد بهتر است در ویو هندل شود، چون به request.data نیاز دارد
        pass