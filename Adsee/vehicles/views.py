from rest_framework import viewsets, permissions
from .models import VehicleType, Vehicle
from .serializers import (
    VehicleTypeSerializer,
    VehicleListSerializer,
    VehicleDetailSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_staff

class VehicleTypeViewSet(viewsets.ModelViewSet):
    queryset = VehicleType.objects.filter(is_active=True)
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAdminOrReadOnly]    # همه کاربران می‌تونن ببینن، فقط ادمین تغییر بده


class VehicleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return VehicleListSerializer
        return VehicleDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Vehicle.objects.all()
        return Vehicle.objects.filter(driver=user)

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user)