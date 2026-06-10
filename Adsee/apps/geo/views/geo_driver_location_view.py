from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from geo.serializers import (
    DriverLocationCreateSerializer,
    DriverLocationReadSerializer,
    BatchLocationSerializer,
)
from geo.models import DriverLocation
from utils.permissions import IsDriverOrAdmin
from geo.services import DriverLocationService


class DriverLocationViewSet(viewsets.ModelViewSet):
    """
    مدیریت موقعیت‌های مکانی راننده.

    ### متدهای اصلی:
    - **GET /geo/driver-locations/**: لیست موقعیت‌ها (ادمین: همه، راننده: فقط خودش)
    - **POST /geo/driver-locations/**: ارسال موقعیت لحظه‌ای (real-time)
      - Body: `{"point": {"type": "Point", "coordinates": [51.39, 35.70]}}`
      - به‌طور خودکار به سفر فعال متصل می‌شود

    ### اکشن‌های اختصاصی:
    - **POST /geo/driver-locations/batch/**: ارسال دسته‌ای موقعیت‌ها (آفلاین)
      - Body: `{"trip_id": 1, "points": [{"lat": 35.70, "lon": 51.39, "timestamp": 1715172000, "speed": 40, "heading": 90}, ...]}`
      - نقاط با source='batch' ذخیره می‌شوند

    ### محدودیت‌ها:
    - فقط کاربران با نقش DRIVER دسترسی دارند.
    """
    permission_classes = [permissions.IsAuthenticated, IsDriverOrAdmin]
    queryset = DriverLocation.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return DriverLocationCreateSerializer
        return DriverLocationReadSerializer

    def get_queryset(self):
        return DriverLocationService.get_queryset(self.request.user)

    def perform_create(self, serializer):
        # Save the location directly (serializer handles the point)
        serializer.save(driver=self.request.user)

    @action(detail=False, methods=['post'], url_path='batch')
    def batch_upload(self, request):
        """ارسال دسته‌ای موقعیت‌ها"""
        serializer = BatchLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trip_id = serializer.validated_data['trip_id']
        points = serializer.validated_data['points']

        try:
            created_locations = DriverLocationService.create_batch_locations(
                user=request.user,
                trip_id=trip_id,
                points=points
            )
            return Response({
                'received': len(created_locations),
                'locations': created_locations
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)