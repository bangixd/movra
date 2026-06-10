from geo.models import Province


class ProvinceService:
    """سرویس مدیریت استان‌ها"""

    @staticmethod
    def get_all_provinces():
        """برگرداندن همهٔ استان‌ها"""
        return Province.objects.all()