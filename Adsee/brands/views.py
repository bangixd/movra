from rest_framework import viewsets, permissions
from .models import Brand
from .serializers import BrandListSerializer, BrandDetailSerializer
from permissions import IsClientUser, IsOwnerOrAdmin


class BrandViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsClientUser, IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return BrandListSerializer
        return BrandDetailSerializer

    def get_queryset(self):
        # هر کلاینت فقط برندهای خودش رو می‌بینه
        user = self.request.user
        if not user.is_authenticated:
            return Brand.objects.none()
        return Brand.objects.filter(client=self.request.user.client_profile)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user.client_profile)
