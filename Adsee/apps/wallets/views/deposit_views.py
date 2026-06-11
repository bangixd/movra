from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from decimal import Decimal
from wallets.services.deposit_service import DepositService
from wallets.models import Wallet


class DepositView(APIView):
    """
    شارژ کیف پول.

    POST /wallet/deposit/
    Body: {"amount": 500000}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # ۱. اعتبارسنجی مبلغ
        amount_str = request.data.get('amount')
        if not amount_str:
            return Response({"error": "مبلغ شارژ الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(amount_str)
        except (ValueError, TypeError):
            return Response({"error": "مبلغ نامعتبر"}, status=status.HTTP_400_BAD_REQUEST)

        # ۲. فراخوانی سرویس
        try:
            result = DepositService.request_deposit(request.user, amount)
            return Response(result, status=status.HTTP_200_OK)
        except Wallet.DoesNotExist:
            return Response({"error": "کیف پولی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)