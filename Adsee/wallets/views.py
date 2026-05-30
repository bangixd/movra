from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wallet, Transaction, BankAccount
from .serializers import TransactionSerializer, WalletSummarySerializer, BankAccountSerializer
from permissions import IsDriverUser

class WalletViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class= WalletSummarySerializer


    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """خلاصه وضعیت مالی (درآمد کل، موجودی، شماره کارت)"""
        wallet = self.get_queryset().first()
        if not wallet:
            return Response({"error": "کیف پولی یافت نشد"}, status=404)
        serializer = WalletSummarySerializer(wallet)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """لیست تراکنش‌های راننده"""
        wallet = self.get_queryset().first()
        if not wallet:
            return Response({"error": "کیف پولی یافت نشد"}, status=404)
        txs = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
        serializer = TransactionSerializer(txs, many=True)
        return Response(serializer.data)


class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BankAccount.objects.filter(driver__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user.driver_profile)
