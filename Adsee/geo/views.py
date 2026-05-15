from rest_framework import viewsets, permissions
from .models import Province, City, Neighborhood, SuggestedRoute, DriverLocation
from trips.models import Trip
from .serializers import (
    ProvinceSerializer, CitySerializer, CityListSerializer,
    NeighborhoodSerializer, SuggestedRouteSerializer,
    DriverLocationCreateSerializer, DriverLocationReadSerializer
)
from permissions import IsDriverUser


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
            driver=self.request.user
        ).exclude(
            status__in=[Trip.Status.COMPLETED, Trip.Status.CANCELLED]
        ).first()
        serializer.save(driver=self.request.user.driver_profile, trip=active_trip)
