from rest_framework import viewsets, permissions
from .models import VehicleType, Vehicle
from .serializers import (
    VehicleTypeSerializer,
    VehicleListSerializer,
    VehicleDetailSerializer,
)
from ..core.permissions import IsAdminOrReadOnly, IsDriverUser


class VehicleTypeViewSet(viewsets.ModelViewSet):
    queryset = VehicleType.objects.filter(is_active=True)
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class VehicleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsDriverUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return VehicleListSerializer
        return VehicleDetailSerializer

    def get_queryset(self):
        user = self.request.user.driver_profile
        if user.is_staff:
            return Vehicle.objects.all()
        return Vehicle.objects.filter(driver=user)

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user)
