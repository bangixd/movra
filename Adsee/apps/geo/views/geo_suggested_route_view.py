from rest_framework import viewsets, permissions
from geo.serializers import SuggestedRouteSerializer
from geo.services import SuggestedRouteService


class SuggestedRouteViewSet(viewsets.ModelViewSet):
    """
    مدیریت مسیرهای پیشنهادی.

    ### متدهای اصلی:
    - **GET /geo/routes/**: لیست همهٔ مسیرهای پیشنهادی (همهٔ کاربران لاگین‌شده)
    - **POST /geo/routes/**: ایجاد مسیر جدید (فقط ادمین)
      - Body: `{"name": "مسیر شماره ۱", "city": 1, "description": "...", "path": "LINESTRING(51.0 35.0, 51.1 35.1)"}`
    - **GET /geo/routes/{id}/**: جزئیات یک مسیر
    - **PUT/PATCH /geo/routes/{id}/**: ویرایش مسیر (فقط ادمین)
    - **DELETE /geo/routes/{id}/**: حذف مسیر (فقط ادمین)

    ### محدودیت‌ها:
    - خواندن: همهٔ کاربران احراز هویت‌شده
    - نوشتن: فقط ادمین
    """
    serializer_class = SuggestedRouteSerializer
    queryset = SuggestedRouteService.get_all_routes()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]