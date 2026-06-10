from rest_framework import viewsets, permissions
from geo.serializers import CityListSerializer, CitySerializer
from geo.services import CityService


class CityViewSet(viewsets.ModelViewSet):
    """
    مدیریت شهرها.

    ### متدهای اصلی:
    - **GET /geo/cities/**: لیست همهٔ شهرها (همهٔ کاربران لاگین‌شده)
      - از `CityListSerializer` (خلاصه) استفاده می‌کند
    - **POST /geo/cities/**: ایجاد شهر جدید (فقط ادمین)
      - Body: `{"name": "تهران", "province": 1, "center": "POINT(51.38 35.68)"}`
    - **GET /geo/cities/{id}/**: جزئیات یک شهر (با `CitySerializer` کامل)
    - **PUT/PATCH /geo/cities/{id}/**: ویرایش شهر (فقط ادمین)
    - **DELETE /geo/cities/{id}/**: حذف شهر (فقط ادمین)

    ### محدودیت‌ها:
    - خواندن: همهٔ کاربران احراز هویت‌شده
    - نوشتن: فقط ادمین
    """
    queryset = CityService.get_all_cities()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CityListSerializer
        return CitySerializer