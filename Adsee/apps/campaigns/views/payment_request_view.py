from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from campaigns.models import Campaign
from campaigns.services import PaymentService
from utils.permissions import IsClientUser


class PaymentRequestView(APIView):
    """
    شروع فرآیند پرداخت برای یک کمپین
    """
    permission_classes = [permissions.IsAuthenticated, IsClientUser]

    def post(self, request):
        # ۱. اعتبارسنجی اولیه
        campaign_id = request.data.get('campaign_id')
        if not campaign_id:
            return Response(
                {"error": "شناسهٔ کمپین الزامی است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ۲. یافتن کمپین و بررسی مالکیت
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            brand_name__client__user=request.user
        )

        # ۳. ایجاد یا یافتن فاکتور
        try:
            invoice = PaymentService.create_or_get_invoice(campaign)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # ۴. شروع پرداخت
        try:
            result = PaymentService.initiate_payment(
                invoice, campaign, request.user.phone
            )
            return Response(result, status=status.HTTP_200_OK)
        except ConnectionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)