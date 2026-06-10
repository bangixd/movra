from rest_framework import viewsets, permissions
from print_shops.serializers import PrintShopProfileSerializer
from print_shops.services import PrintShopProfileService
from utils.permissions import IsPrintShopUser


class PrintShopProfileViewSet(viewsets.ModelViewSet):
    """
    مدیریت پروفایل چاپخانه.

    ### متدهای اصلی:
    - **GET /printshop/**: لیست پروفایل‌ها (ادمین: همه، چاپخانه: فقط خودش)
    - **POST /printshop/**: ایجاد پروفایل جدید
      - Body: `{"shop_name": "چاپخانه تست", "address": "...", "phone": "...", "location": "POINT(51.38 35.68)"}`
    - **GET /printshop/{id}/**: جزئیات یک پروفایل
    - **PUT/PATCH /printshop/{id}/**: ویرایش پروفایل
    - **DELETE /printshop/{id}/**: حذف پروفایل

    ### محدودیت‌ها:
    - فقط کاربران با نقش PRINT_SHOP و ادمین دسترسی دارند.
    - هر چاپخانه فقط پروفایل خود را می‌تواند ویرایش کند.
    """
    serializer_class = PrintShopProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsPrintShopUser]

    def get_queryset(self):
        return PrintShopProfileService.get_queryset(self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)