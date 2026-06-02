from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from decimal import Decimal
from rest_framework.response import Response
from .models import Wallet, Transaction, BankAccount
from .serializers import TransactionSerializer, WalletSummarySerializer, BankAccountSerializer

class WalletViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BankAccount.objects.filter(driver__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user.driver_profile)

class WithdrawalRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        print('amount', amount)
        if not amount:
            return Response({"error": "مبلغ برداشت الزامی است"}, status=400)
        try:
            amount = Decimal(amount)
        except:
            return Response({"error": "مبلغ نامعتبر"}, status=400)

        wallet = request.user.wallet
        print(wallet.balance,' balance')
        if wallet.balance < amount:
            return Response({"error": "موجودی کافی نیست"}, status=400)

        # ثبت تراکنش برداشت
        Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            status=Transaction.Status.PENDING,   # نیاز به تأیید ادمین
            description='درخواست برداشت از حساب'
        )

        # کسر موقت از موجودی (بسته به سیاست شما می‌تواند بعد از تأیید ادمین کم شود)
        wallet.balance -= amount
        wallet.save()

        return Response({"message": "درخواست برداشت ثبت شد و پس از تأیید ادمین انجام می‌شود"}, status=200)

class DepositView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        if not amount:
            return Response({"error": "مبلغ شارژ الزامی است"}, status=400)
        try:
            amount = Decimal(amount)
        except:
            return Response({"error": "مبلغ نامعتبر"}, status=400)

        wallet = request.user.wallet

        # ثبت تراکنش شارژ
        Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            status=Transaction.Status.SUCCESS,
            description='شارژ کیف پول'
        )

        wallet.balance += amount
        wallet.save()

        return Response({"message": f"کیف پول با موفقیت {amount} تومان شارژ شد", "balance": wallet.balance}, status=200)