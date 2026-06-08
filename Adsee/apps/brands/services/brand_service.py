from brands.models import Brand


class BrandService:
    """سرویس مدیریت برندها"""

    @staticmethod
    def get_queryset(user, status_param=None):
        """
        برگرداندن برندها بر اساس نقش کاربر و فیلتر وضعیت.
        - ادمین: همهٔ برندها
        - کلاینت: فقط برندهای خودش
        """
        if not user.is_authenticated:
            return Brand.objects.none()

        if user.is_staff:
            qs = Brand.objects.all()
        else:
            qs = Brand.objects.filter(client__user=user)

        if status_param:
            qs = qs.filter(status=status_param.upper())

        return qs

    @staticmethod
    def create_brand(user, validated_data: dict) -> Brand:
        """
        ایجاد برند جدید برای کلاینت با وضعیت PENDING.
        """
        validated_data['client'] = user.client_profile
        validated_data['status'] = 'PENDING'
        return Brand.objects.create(**validated_data)

    @staticmethod
    def review_brand(brand, new_status: str) -> Brand:
        """
        بررسی برند توسط ادمین (تأیید یا رد).
        Args:
            brand: نمونهٔ برند
            new_status: APPROVED یا REJECTED
        Returns:
            برند به‌روزرسانی‌شده
        Raises:
            ValueError: اگر وضعیت نامعتبر باشد
        """
        valid_statuses = ['APPROVED', 'REJECTED']
        if new_status not in valid_statuses:
            raise ValueError("وضعیت نامعتبر است")

        brand.status = new_status
        brand.save()
        return brand