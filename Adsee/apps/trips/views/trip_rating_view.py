from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from trips.services.trip_rating_service import TripRatingService
from trips.models import Trip
from utils.permissions import IsClientUser

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsClientUser])
def rate_driver(request, trip_id):
    rating = request.data.get('rating')
    feedback = request.data.get('feedback', '')
    try:
        TripRatingService.rate_trip(request.user, trip_id, int(rating), feedback)
        return Response({"message": "امتیاز با موفقیت ثبت شد"})
    except Trip.DoesNotExist:
        return Response({"error": "سفر یافت نشد یا متعلق به شما نیست"}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)