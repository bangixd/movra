from rest_framework import viewsets
from .models import BrandCategory
from .serializers import AdminBrandCategorySerializer
from utils.permissions import IsAdminUser

class AdminBrandCategoryViewSet(viewsets.ModelViewSet):
    queryset = BrandCategory.objects.all()
    serializer_class = AdminBrandCategorySerializer
    permission_classes = [IsAdminUser]