from support.models import FAQCategory, AppDownloadLink, SiteSetting, SupportContent


class SupportService:
    """سرویس مدیریت محتوای پشتیبانی (عمومی)"""

    @staticmethod
    def get_active_content(content_type=None):
        """برگرداندن محتوای پشتیبانی فعال"""
        queryset = SupportContent.objects.filter(is_active=True)
        if content_type:
            queryset = queryset.filter(type=content_type.upper())
        return queryset

    @staticmethod
    def get_active_site_settings():
        """برگرداندن اولین تنظیمات فعال سایت"""
        return SiteSetting.objects.filter(is_active=True).first()

    @staticmethod
    def get_faq_categories():
        """برگرداندن دسته‌بندی‌های فعال FAQ"""
        return FAQCategory.objects.filter(is_active=True).prefetch_related('faqs')

    @staticmethod
    def get_app_download_links():
        """برگرداندن لینک‌های دانلود فعال"""
        return AppDownloadLink.objects.filter(is_active=True)

    @staticmethod
    def get_site_setting():
        """برگرداندن اولین رکورد تنظیمات (برای ادمین)"""
        return SiteSetting.objects.first()

    @staticmethod
    def get_active_site_settings():
        """برگرداندن اولین رکورد فعال (برای نمایش عمومی)"""
        return SiteSetting.objects.filter(is_active=True).first()