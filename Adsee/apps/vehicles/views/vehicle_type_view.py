from rest_framework import viewsets
from vehicles.serializers import VehicleTypeSerializer
from vehicles.services.vehicle_type_service import VehicleTypeService
from utils.permissions import IsAdminOrReadOnly


class VehicleTypeViewSet(viewsets.ModelViewSet):
    """
    مدیریت انواع خودرو.

    ### متدهای اصلی:
    - **GET /vehicles/types/**: لیست انواع خودرو فعال (همهٔ کاربران لاگین‌شده)
    - **POST /vehicles/types/**: ایجاد نوع خودرو جدید (فقط ادمین)
    - **GET /vehicles/types/{id}/**: جزئیات یک نوع خودرو
    - **PUT/PATCH /vehicles/types/{id}/**: ویرایش (فقط ادمین)
    - **DELETE /vehicles/types/{id}/**: حذف (فقط ادمین)

    ### محدودیت‌ها:
    - خواندن: همهٔ کاربران احراز هویت‌شده
    - نوشتن: فقط ادمین
    """
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return VehicleTypeService.get_active_types()