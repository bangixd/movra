from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from brands.models import Brand
from brands.serializers import BrandListSerializer, BrandCreateUpdateSerializer, BrandDetailSerializer
from brands.services.brand_service import BrandService
from utils.permissions import IsClientUser, IsAdminUser


class BrandViewSet(viewsets.ModelViewSet):
    """
    مدیریت برندها (CRUD).

    ### متدهای اصلی:
    - **GET /brands/**: لیست برندها
      - پارامتر اختیاری Query: `status` (مقادیر: APPROVED, REJECTED, PENDING)
      - ادمین: همهٔ برندها، کلاینت: فقط برندهای خودش
    - **POST /brands/**: ایجاد برند جدید (وضعیت اولیه: PENDING)
      - Body: `{"name": "برند تست", "slug": "test-brand", ...}`
    - **GET /brands/{id}/**: جزئیات یک برند
    - **PUT/PATCH /brands/{id}/**: ویرایش برند
    - **DELETE /brands/{id}/**: حذف برند

    ### اکشن‌های اختصاصی:
    - **PATCH /brands/{id}/review/**: بررسی برند (فقط ادمین)
      - Body: `{"status": "APPROVED"}` یا `{"status": "REJECTED"}`
      - Response: اطلاعات برند به‌روزرسانی‌شده

    ### محدودیت‌ها:
    - فقط کاربران با نقش CLIENT و ادمین دسترسی دارند.
    - بررسی برند فقط توسط ادمین.
    """

    def get_permissions(self):
        if self.action == 'review':
            return [IsAdminUser()]
        return [permissions.IsAuthenticated(), IsClientUser()]

    def get_serializer_class(self):
        if self.action == 'list':
            return BrandListSerializer
        if self.action == 'retrieve':
            return BrandDetailSerializer  # یا هر نامی که دارد
        return BrandCreateUpdateSerializer

    def get_queryset(self):
        user = self.request.user
        status_param = self.request.query_params.get('status')
        return BrandService.get_queryset(user, status_param)

    def perform_create(self, serializer):
        # استفاده از سرویس برای ایجاد برند
        brand = BrandService.create_brand(
            user=self.request.user,
            validated_data=serializer.validated_data
        )
        serializer.instance = brand

    @action(detail=True, methods=['patch'])
    def review(self, request, pk=None):
        """بررسی برند توسط ادمین"""
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        brand = self.get_object()
        new_status = request.data.get('status')

        try:
            updated_brand = BrandService.review_brand(brand, new_status)
            serializer = self.get_serializer(updated_brand)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)