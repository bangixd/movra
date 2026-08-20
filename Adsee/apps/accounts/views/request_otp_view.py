from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from django.conf import settings

from accounts.serializers import OTPRequestSerializer
from accounts.services import OTPService


class RequestOTPView(APIView):
    """
    API برای درخواست کد احراز هویت.

    در صورت نیاز کاربر جدید ساخته می‌شود و کد OTP از طریق پیامک ارسال می‌گردد.

    **POST** `/v1/auth/otp/`

    **Body** (JSON):
    ```json
    {
        "identifier": "09121111111",
        "purpose": "REGISTER"       // اختیاری، پیش‌فرض LOGIN
    }
    """
    serializer_class = OTPRequestSerializer
    throttle_classes = [AnonRateThrottle]
    permission_classes = []
    throttle_scope = 'otp_request'

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        identifier = serializer.validated_data['identifier']
        purpose = serializer.validated_data['purpose']

        try:
            # فراخوانی سرویس
            otp, user_created = OTPService.request_otp(identifier, purpose)
        except Exception as e:
            # خطا در ارسال SMS یا سایر موارد
            return Response(
                {"detail": "خطا در ارسال کد تأیید. لطفاً مجدداً تلاش کنید."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "detail": f"کد تأیید به {identifier} ارسال شد. "
                          f"این کد تا {settings.OTP_CODE_EXPIRY_MINUTES} دقیقه معتبر است."
                          f"code {otp.code}"

            },
            status=status.HTTP_200_OK
        )