from wallets.models import BankAccount


class BankAccountService:
    """سرویس مدیریت حساب‌های بانکی"""

    @staticmethod
    def get_queryset(user):
        """
        برگرداندن حساب‌های بانکی کاربر.
        - کاربر عادی: فقط حساب‌های خودش (بر اساس driver_profile)
        - ادمین: همهٔ حساب‌ها (اختیاری)
        """
        if not user.is_authenticated:
            return BankAccount.objects.none()
        # اگر روزی خواستید ادمین همه را ببیند، شرط is_staff را اضافه کنید
        return BankAccount.objects.filter(driver__user=user)

    @staticmethod
    def create_bank_account(user, validated_data: dict) -> BankAccount:
        """
        ایجاد حساب بانکی جدید برای راننده.
        """
        validated_data['driver'] = user.driver_profile
        return BankAccount.objects.create(**validated_data)