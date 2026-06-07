from rest_framework import viewsets, status, permissions
from rest_framework.permissions import IsAuthenticated
from brands.models import BrandCategory
from brands.serializers import BrandCategorySerializer
from utils.permissions import IsClientUser, IsAdminUser

class BrandCategoryListView(viewsets.ReadOnlyModelViewSet):
    queryset = BrandCategory.objects.filter(is_active=True)
    serializer_class = BrandCategorySerializer
    permission_classes = [IsAuthenticated, IsClientUser]
