from geo.models import City


class CityService:
    """سرویس مدیریت شهرها"""

    @staticmethod
    def get_all_cities():
        """برگرداندن همهٔ شهرها"""
        return City.objects.all()