from vehicles.models import Vehicle


class VehicleService:
    """سرویس مدیریت خودروها"""

    @staticmethod
    def get_queryset(user):
        """
        برگرداندن خودروها بر اساس نقش کاربر.
        - ادمین: همهٔ خودروها
        - راننده: فقط خودروهای خودش
        """
        if not user.is_authenticated:
            return Vehicle.objects.none()
        if user.is_staff:
            return Vehicle.objects.all()
        # راننده: پروفایل راننده باید وجود داشته باشد
        if hasattr(user, 'driver_profile'):
            return Vehicle.objects.filter(driver=user.driver_profile)
        return Vehicle.objects.none()

    @staticmethod
    def create_vehicle(user, validated_data: dict) -> Vehicle:
        """
        ایجاد خودرو جدید برای راننده.
        """
        validated_data['driver'] = user.driver_profile
        return Vehicle.objects.create(**validated_data)