from rest_framework import viewsets, permissions
from .models import Brand
from .serializers import BrandListSerializer, BrandDetailSerializer
from ..core.permissions import IsClientUser


class BrandViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClientUser]

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