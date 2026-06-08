from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from clients.services.geocoding_service import GeocodingService
from utils.permissions import IsClientUser


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsClientUser])
def reverse_geocode(request):
    """
    تبدیل مختصات جغرافیایی به آدرس (Reverse Geocoding) با استفاده از سرویس نشان.

    ### POST /clients/reverse-geocode/
    Body:
    ```json
    {
        "lat": 35.6892,
        "lng": 51.3890
    }
    """
    lat = request.data.get('lat')
    lng = request.data.get('lng')

    try:
        result = GeocodingService.reverse_geocode(lat, lng)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except ConnectionError as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)