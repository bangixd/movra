from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drivers.models import DriverProfile
from drivers.serializers import DriverProfileSerializer
from drivers.services.driver_profile_service import DriverProfileService
from utils.permissions import IsDriverOrAdmin


class DriverProfileViewSet(viewsets.ModelViewSet):
    """
    مدیریت پروفایل راننده (CRUD).

    ### متدهای اصلی:
    - **GET /drivers/profile/**: لیست پروفایل‌ها (ادمین: همه، راننده: فقط خودش)
    - **POST /drivers/profile/**: ایجاد پروفایل جدید
    - **GET /drivers/profile/{id}/**: جزئیات یک پروفایل
    - **PUT/PATCH /drivers/profile/{id}/**: ویرایش پروفایل
    - **DELETE /drivers/profile/{id}/**: حذف پروفایل

    ### اکشن‌های اختصاصی:
    - **PATCH /drivers/profile/accept_contract/**: پذیرش قرارداد (مرحلهٔ ۴ ثبت‌نام)
      - نیاز به kyc_status=APPROVED دارد
      - Response: اطلاعات پروفایل به‌روزرسانی‌شده

    - **GET /drivers/profile/referral_summary/**: خلاصهٔ دعوت‌ها و جوایز معرف
      - Response: `{"referral_code": "...", "invited_count": 5, "total_rewards": 500000, "rewards": [...]}`

    ### محدودیت‌ها:
    - فقط کاربران با نقش DRIVER و ادمین دسترسی دارند.
    - هر راننده فقط پروفایل خود را می‌تواند ویرایش کند.
    """
    serializer_class = DriverProfileSerializer
    permission_classes = [IsAuthenticated, IsDriverOrAdmin]

    def get_queryset(self):
        return DriverProfileService.get_queryset(self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['patch'])
    def accept_contract(self, request):
        """مرحلهٔ ۴: پذیرش قرارداد"""
        profile = DriverProfileService.get_profile(request.user)
        if not profile:
            return Response({"error": "پروفایلی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        try:
            updated_profile = DriverProfileService.accept_contract(profile)
            serializer = self.get_serializer(updated_profile)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def referral_summary(self, request):
        """خلاصهٔ دعوت‌ها و جوایز معرف"""
        driver = request.user.driver_profile
        data = DriverProfileService.get_referral_summary(driver)
        return Response(data)