from rest_framework import viewsets, permissions
from geo.serializers import ProvinceSerializer
from geo.services import ProvinceService


class ProvinceViewSet(viewsets.ModelViewSet):
    """
    مدیریت استان‌ها.

    ### متدهای اصلی:
    - **GET /geo/provinces/**: لیست همهٔ استان‌ها (همهٔ کاربران لاگین‌شده)
    - **POST /geo/provinces/**: ایجاد استان جدید (فقط ادمین)
    - **GET /geo/provinces/{id}/**: جزئیات یک استان
    - **PUT/PATCH /geo/provinces/{id}/**: ویرایش استان (فقط ادمین)
    - **DELETE /geo/provinces/{id}/**: حذف استان (فقط ادمین)

    ### محدودیت‌ها:
    - خواندن: همهٔ کاربران احراز هویت‌شده
    - نوشتن: فقط ادمین
    """
    serializer_class = ProvinceSerializer
    queryset = ProvinceService.get_all_provinces()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]