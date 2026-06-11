from decimal import Decimal
from wallets.models import Transaction


class WithdrawalService:
    """سرویس مدیریت درخواست‌های برداشت"""

    @staticmethod
    def request_withdrawal(user, amount: Decimal) -> dict:
        """
        ثبت درخواست برداشت.
        Args:
            user: کاربر درخواست‌دهنده
            amount: مبلغ به تومان (Decimal)
        Returns:
            dict: {'message': '...'}
        Raises:
            ValueError: اگر مبلغ نامعتبر یا موجودی ناکافی باشد
            Wallet.DoesNotExist: اگر کاربر کیف پول نداشته باشد
        """
        wallet = user.wallet  # اگر وجود نداشته باشد، خطای RelatedObjectDoesNotExist می‌دهد

        if amount <= 0:
            raise ValueError("مبلغ نامعتبر")

        if wallet.balance < amount:
            raise ValueError("موجودی کافی نیست")

        # ثبت تراکنش برداشت
        Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            status=Transaction.Status.PENDING,   # نیاز به تأیید ادمین
            description='درخواست برداشت از حساب'
        )

        # کسر موقت از موجودی (بسته به سیاست می‌تواند بعد از تأیید ادمین کم شود)
        wallet.balance -= amount
        wallet.save()

        return {"message": "درخواست برداشت ثبت شد و پس از تأیید ادمین انجام می‌شود"}