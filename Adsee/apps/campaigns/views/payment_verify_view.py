from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from campaigns.models import PaymentTransaction
from campaigns.services import PaymentService


class PaymentVerifyView(APIView):
    """
    Callback از درگاه زرین‌پال برای تأیید پرداخت.

    ### GET /campaigns/payments/verify/?Authority=...&Status=OK
    این endpoint توسط زرین‌پال فراخوانی می‌شود و نیازی به احراز هویت ندارد.

    ### پارامترهای Query:
    - `Authority`: شناسهٔ یکتای تراکنش (از زرین‌پال)
    - `Status`: وضعیت پرداخت (`OK` یا `NOK`)

    ### نمونه پاسخ موفق:
    ```json
    {
        "message": "پرداخت موفق بود",
        "ref_id": "123456789",
        "status": "success"
    }
    خطاها:
400: پارامترها نامعتبر، تراکنش ناموفق، یا پرداخت لغو شده

404: تراکنش با این Authority یافت نشد

نکات:
    پس از پرداخت موفق، کمپین فعال می‌شود.

    تغییرات مربوط به فاکتور (تمدید، افزایش خودرو، تغییر طراحی) اعمال می‌شود.
    """
    permission_classes = []  # زرین‌پال احراز هویت ندارد

    def get(self, request):
        authority = request.query_params.get('Authority')
        status_param = request.query_params.get('Status')

        # ۱. اعتبارسنجی پارامترها
        if not authority or not status_param:
            return Response(
                {"error": "پارامترها نامعتبر"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ۲. فراخوانی سرویس
        try:
            result = PaymentService.verify_payment(authority, status_param)
            if 'error' in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            return Response(result, status=status.HTTP_200_OK)
        except PaymentTransaction.DoesNotExist:
            return Response(
                {"error": "تراکنش یافت نشد"},
                status=status.HTTP_404_NOT_FOUND
            )