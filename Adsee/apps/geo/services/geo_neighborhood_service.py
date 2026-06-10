from geo.models import Neighborhood


class NeighborhoodService:
    """سرویس مدیریت محله‌ها"""

    @staticmethod
    def get_all_neighborhoods():
        """برگرداندن همهٔ محله‌ها"""
        return Neighborhood.objects.all()