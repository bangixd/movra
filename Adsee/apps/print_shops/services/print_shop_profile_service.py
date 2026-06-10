from print_shops.models import PrintShopProfile


class PrintShopProfileService:
    """سرویس مدیریت پروفایل چاپخانه"""

    @staticmethod
    def get_queryset(user):
        """
        برگرداندن پروفایل‌ها بر اساس نقش کاربر.
        - ادمین: همهٔ پروفایل‌ها
        - چاپخانه: فقط پروفایل خودش
        """
        if not user.is_authenticated:
            return PrintShopProfile.objects.none()
        if user.is_staff:
            return PrintShopProfile.objects.all()
        return PrintShopProfile.objects.filter(user=user)

    @staticmethod
    def create_profile(user, validated_data: dict) -> PrintShopProfile:
        """
        ایجاد پروفایل جدید برای چاپخانه.
        """
        validated_data['user'] = user
        return PrintShopProfile.objects.create(**validated_data)