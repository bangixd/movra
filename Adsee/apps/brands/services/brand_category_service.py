from brands.models import BrandCategory

class BrandCategoryService:
    """سرویس مدیریت دسته‌بندی برندها"""

    @staticmethod
    def get_active_categories():
        """برگرداندن دسته‌بندی‌های فعال"""
        return BrandCategory.objects.filter(is_active=True)