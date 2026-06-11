from vehicles.models import VehicleType


class VehicleTypeService:
    """سرویس مدیریت انواع خودرو"""

    @staticmethod
    def get_active_types():
        """برگرداندن انواع خودرو فعال"""
        return VehicleType.objects.filter(is_active=True)