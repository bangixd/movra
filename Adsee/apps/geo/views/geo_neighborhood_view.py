from rest_framework import viewsets, permissions
from geo.serializers import NeighborhoodSerializer
from geo.services import NeighborhoodService


class NeighborhoodViewSet(viewsets.ModelViewSet):
    """
    مدیریت محله‌ها.

    ### متدهای اصلی:
    - **GET /geo/neighborhoods/**: لیست همهٔ محله‌ها (همهٔ کاربران لاگین‌شده)
    - **POST /geo/neighborhoods/**: ایجاد محلهٔ جدید (فقط ادمین)
      - Body: `{"name": "نیاوران", "city": 1, "center": "POINT(51.45 35.80)", "radius_meter": 2500}`
    - **GET /geo/neighborhoods/{id}/**: جزئیات یک محله
    - **PUT/PATCH /geo/neighborhoods/{id}/**: ویرایش محله (فقط ادمین)
    - **DELETE /geo/neighborhoods/{id}/**: حذف محله (فقط ادمین)

    ### محدودیت‌ها:
    - خواندن: همهٔ کاربران احراز هویت‌شده
    - نوشتن: فقط ادمین
    """
    serializer_class = NeighborhoodSerializer
    queryset = NeighborhoodService.get_all_neighborhoods()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]