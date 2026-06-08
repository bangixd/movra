from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drivers.services.driver_profile_service import DriverProfileService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_referral_code(request):
    """
    ثبت کد معرف برای راننده.

    ### POST /drivers/apply-referral/
    Body:
    ```json
    {
        "referral_code": "ABC123"
    }
    """
    code = request.data.get('referral_code')

    try:
        result = DriverProfileService.apply_referral_code(request.user, code)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)