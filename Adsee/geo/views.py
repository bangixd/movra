# apps/geo/views.py
from rest_framework import viewsets, permissions
from .models import Province, City, Neighborhood, SuggestedRoute, DriverLocation
from trips.models import Trip
from .serializers import (
    ProvinceSerializer, CitySerializer, CityListSerializer,
    NeighborhoodSerializer, SuggestedRouteSerializer,
    DriverLocationCreateSerializer, DriverLocationReadSerializer
)


class ProvinceViewSet(viewsets.ModelViewSet):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer
    permission_classes = [permissions.IsAuthenticated]  # هر کاربر وارد شده


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return CityListSerializer
        return CitySerializer


class NeighborhoodViewSet(viewsets.ModelViewSet):
    queryset = Neighborhood.objects.all()
    serializer_class = NeighborhoodSerializer
    permission_classes = [permissions.IsAuthenticated]


class SuggestedRouteViewSet(viewsets.ModelViewSet):
    queryset = SuggestedRoute.objects.all()
    serializer_class = SuggestedRouteSerializer
    permission_classes = [permissions.IsAuthenticated]


class DriverLocationViewSet(viewsets.ModelViewSet):
    # فقط راننده‌ها می‌تونن لوکیشن ثبت کنن
    permission_classes = [permissions.IsAuthenticated]
    queryset = DriverLocation.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return DriverLocationCreateSerializer
        return DriverLocationReadSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return DriverLocation.objects.all()
        return DriverLocation.objects.filter(driver=user)

    def perform_create(self, serializer):
        active_trip = Trip.objects.filter(
            driver=self.request.user
        ).exclude(
            status__in=[Trip.Status.COMPLETED, Trip.Status.CANCELLED]
        ).first()
        serializer.save(driver=self.request.user, trip=active_trip)