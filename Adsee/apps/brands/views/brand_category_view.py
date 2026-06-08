from rest_framework import viewsets, permissions
from brands.serializers import BrandCategorySerializer
from brands.services.brand_category_service import BrandCategoryService
from utils.permissions import IsClientUser


class BrandCategoryListView(viewsets.ReadOnlyModelViewSet):
    """
    لیست دسته‌بندی‌های فعال برندها (فقط خواندنی).

    ### متدها:
    - **GET /brands/categories/**: لیست همهٔ دسته‌بندی‌های فعال
    - **GET /brands/categories/{id}/**: جزئیات یک دسته‌بندی

    ### محدودیت‌ها:
    - فقط کاربران لاگین‌شده با نقش CLIENT دسترسی دارند.
    """
    serializer_class = BrandCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsClientUser]

    def get_queryset(self):
        return BrandCategoryService.get_active_categories()
