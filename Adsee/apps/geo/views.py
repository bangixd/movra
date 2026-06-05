from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Province, City, Neighborhood, SuggestedRoute, DriverLocation
from trips.models import Trip
from .serializers import (
    ProvinceSerializer, CitySerializer, CityListSerializer,
    NeighborhoodSerializer, SuggestedRouteSerializer,
    DriverLocationCreateSerializer, DriverLocationReadSerializer, BatchLocationSerializer)
from rest_framework.decorators import action
from utils.permissions import IsDriverUser
from django.contrib.gis.geos import Point



class ProvinceViewSet(viewsets.ModelViewSet):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CityListSerializer
        return CitySerializer


class NeighborhoodViewSet(viewsets.ModelViewSet):
    queryset = Neighborhood.objects.all()
    serializer_class = NeighborhoodSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class SuggestedRouteViewSet(viewsets.ModelViewSet):
    queryset = SuggestedRoute.objects.all()
    serializer_class = SuggestedRouteSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class DriverLocationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsDriverUser]
    queryset = DriverLocation.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return DriverLocationCreateSerializer
        return DriverLocationReadSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return DriverLocation.objects.none()
        if user.is_staff:
            return DriverLocation.objects.all()
        return DriverLocation.objects.filter(driver=user)

    def perform_create(self, serializer):
        active_trip = Trip.objects.filter(
            driver=self.request.user.driver_profile
        ).exclude(
            status__in=[Trip.Status.COMPLETED, Trip.Status.CANCELLED]
        ).first()
        serializer.save(driver=self.request.user.driver_profile, trip=active_trip)

    @action(detail=False, methods=['post'], url_path='batch')
    def batch_upload(self, request):
        serializer = BatchLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trip_id = serializer.validated_data['trip_id']
        try:
            trip = Trip.objects.get(id=trip_id, driver__user=request.user)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found or not yours"}, status=404)

        if trip.status not in [Trip.Status.ACTIVE, Trip.Status.PAUSED]:
            return Response({"error": "Trip is not active"}, status=400)

        created_locations = []
        for point in serializer.validated_data['points']:
            lat = point['lat']
            lon = point['lon']
            ts = point.get('timestamp')  # Unix timestamp
            if ts:
                from datetime import datetime, timezone
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            else:
                dt = None

            loc = DriverLocation.objects.create(
                driver=request.user,
                trip=trip,
                point=Point(lon, lat, srid=4326),
                timestamp=dt or timezone.now(),
                source='batch',
                # speed و heading را می‌توان از point گرفت، اما DriverLocation ما این فیلدها را ندارد.
                # می‌توانید آن‌ها را در snapshot یا فیلدهای دیگر ذخیره کنید.
            )
            created_locations.append({
                'id': loc.id,
                'point': {'lat': lat, 'lon': lon},
                'timestamp': loc.timestamp.isoformat()
            })

        #
        # حالا این نقاط را به‌صورت batch به سرویس Analytics بفرستیم (با Celery)
        from services.tasks import forward_batch_locations_task
        forward_batch_locations_task.delay(
            trip_id=trip.id,
            vehicle_plate=trip.vehicle.plate_number,
            campaign_id=trip.campaign.id,
            points=serializer.validated_data['points']
        )

        return Response({
            'received': len(created_locations),
            'locations': created_locations
        }, status=status.HTTP_201_CREATED)
