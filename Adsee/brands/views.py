from rest_framework import viewsets, permissions
from .models import Brand
from .serializers import BrandListSerializer, BrandDetailSerializer

class IsClient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'client_profile')

class BrandViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClient]

    def get_serializer_class(self):
        if self.action == 'list':
            return BrandListSerializer
        return BrandDetailSerializer

    def get_queryset(self):
        # هر کلاینت فقط برندهای خودش رو می‌بینه
        return Brand.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        # client بطور خودکار توی serializer ست می‌شود
        serializer.save()