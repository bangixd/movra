from decimal import Decimal
from wallets.models import Transaction


class DepositService:
    """سرویس مدیریت شارژ کیف پول"""

    @staticmethod
    def request_deposit(user, amount: Decimal) -> dict:
        """
        ثبت درخواست شارژ کیف پول (فوری با وضعیت SUCCESS).
        Args:
            user: کاربر درخواست‌دهنده
            amount: مبلغ به تومان (Decimal)
        Returns:
            dict: {'message': ..., 'balance': ...}
        Raises:
            ValueError: اگر مبلغ نامعتبر باشد
            Wallet.DoesNotExist: اگر کاربر کیف پول نداشته باشد
        """
        wallet = user.wallet  # اگر وجود نداشته باشد، خطا می‌دهد

        if amount <= 0:
            raise ValueError("مبلغ نامعتبر")

        # ثبت تراکنش شارژ
        Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            status=Transaction.Status.SUCCESS,
            description='شارژ کیف پول'
        )

        # افزایش موجودی
        wallet.balance += amount
        wallet.save()

        return {
            "message": f"کیف پول با موفقیت {amount} تومان شارژ شد",
            "balance": wallet.balance
        }