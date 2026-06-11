from rest_framework import viewsets, permissions
from vehicles.serializers import VehicleListSerializer, VehicleDetailSerializer
from vehicles.services.vehicle_service import VehicleService
from utils.permissions import IsDriverUser


class VehicleViewSet(viewsets.ModelViewSet):
    """
    مدیریت خودروهای راننده.

    ### متدهای اصلی:
    - **GET /vehicles/**: لیست خودروها (ادمین: همه، راننده: فقط خودروهای خودش)
      - از `VehicleListSerializer` (خلاصه) استفاده می‌کند
    - **POST /vehicles/**: ثبت خودرو جدید
      - Body: `{"vehicle_type": 1, "plate_number": "12A345B67", ...}`
    - **GET /vehicles/{id}/**: جزئیات خودرو (با `VehicleDetailSerializer`)
    - **PUT/PATCH /vehicles/{id}/**: ویرایش خودرو
    - **DELETE /vehicles/{id}/**: حذف خودرو

    ### محدودیت‌ها:
    - فقط کاربران با نقش DRIVER و ادمین دسترسی دارند.
    - هر راننده فقط خودروهای خود را می‌تواند مدیریت کند.
    """
    permission_classes = [permissions.IsAuthenticated, IsDriverUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return VehicleListSerializer
        return VehicleDetailSerializer

    def get_queryset(self):
        return VehicleService.get_queryset(self.request.user)

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user.driver_profile)