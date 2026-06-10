from geo.models import SuggestedRoute


class SuggestedRouteService:
    """سرویس مدیریت مسیرهای پیشنهادی"""

    @staticmethod
    def get_all_routes():
        """برگرداندن همهٔ مسیرهای پیشنهادی"""
        return SuggestedRoute.objects.all()