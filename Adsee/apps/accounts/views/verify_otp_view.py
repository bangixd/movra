from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle

from accounts.serializers import OTPVerifySerializer
from accounts.services import OTPService
from accounts.models import OTP


class VerifyOTPView(APIView):
    """
    API برای تأیید کد OTP و دریافت توکن JWT
    """
    serializer_class = OTPVerifySerializer
    throttle_classes = [AnonRateThrottle]
    permission_classes = []
    throttle_scope = 'otp_verify'

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        identifier = serializer.validated_data['identifier']
        otp_code = serializer.validated_data['otp']
        purpose = request.data.get('purpose', OTP.Purpose.LOGIN)

        # فراخوانی سرویس
        result, http_status = OTPService.verify_otp(identifier, otp_code, purpose)
        return Response(result, status=http_status)