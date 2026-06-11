from wallets.models import Wallet, Transaction
from wallets.serializers import WalletSummarySerializer, TransactionSerializer


class WalletService:
    """سرویس مدیریت کیف پول و تراکنش‌ها"""

    @staticmethod
    def get_wallet(user) -> Wallet | None:
        """کیف پول کاربر جاری را برمی‌گرداند."""
        return Wallet.objects.filter(user=user).first()

    @staticmethod
    def get_wallet_summary(user) -> dict | None:
        """خلاصهٔ مالی (درآمد کل، موجودی، شماره کارت) را برمی‌گرداند."""
        wallet = WalletService.get_wallet(user)
        if not wallet:
            return None
        serializer = WalletSummarySerializer(wallet)
        return serializer.data

    @staticmethod
    def get_transactions(user) -> list:
        """لیست تراکنش‌های کیف پول کاربر را برمی‌گرداند."""
        wallet = WalletService.get_wallet(user)
        if not wallet:
            return []
        txs = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
        serializer = TransactionSerializer(txs, many=True)
        return serializer.data