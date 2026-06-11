from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from wallets.services.wallet_service import WalletService
from wallets.models import Wallet
from wallets.serializers import WalletSerializer



class WalletViewSet(viewsets.GenericViewSet):
    """
    مدیریت کیف پول و تراکنش‌ها.

    ### اکشن‌ها:
    - **GET /wallet/summary/**: خلاصهٔ مالی (درآمد کل، موجودی، شماره کارت)
    - **GET /wallet/transactions/**: لیست تراکنش‌ها
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WalletSerializer

    def get_queryset(self):
        # همچنان برای استفاده‌های داخلی (مثل router) لازم است
        return Wallet.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """خلاصه وضعیت مالی"""
        data = WalletService.get_wallet_summary(request.user)
        if data is None:
            return Response({"error": "کیف پولی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        return Response(data)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """لیست تراکنش‌ها"""
        data = WalletService.get_transactions(request.user)
        return Response(data)