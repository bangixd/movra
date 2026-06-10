from support.models import (
    SiteSetting, FAQCategory, FAQItem,
    SupportContent, Ticket, AppDownloadLink
)


class SupportAdminService:
    """سرویس مدیریت محتوای پشتیبانی (ادمین)"""

    @staticmethod
    def get_site_setting():
        """همیشه اولین رکورد تنظیمات را برگردان"""
        return SiteSetting.objects.first()

    @staticmethod
    def get_all_site_settings():
        """همهٔ رکوردهای تنظیمات"""
        return SiteSetting.objects.all()

    @staticmethod
    def get_all_faq_categories():
        """همهٔ دسته‌بندی‌های FAQ"""
        return FAQCategory.objects.all().prefetch_related('faqs')

    @staticmethod
    def get_all_faq_items():
        """همهٔ سوالات FAQ"""
        return FAQItem.objects.all().select_related('category')

    @staticmethod
    def get_all_support_content():
        """همهٔ محتوای پشتیبانی"""
        return SupportContent.objects.all()

    @staticmethod
    def get_all_tickets():
        """همهٔ تیکت‌ها"""
        return Ticket.objects.all().select_related('user').order_by('-created_at')

    @staticmethod
    def get_all_app_downloads():
        """همهٔ لینک‌های دانلود"""
        return AppDownloadLink.objects.all()