from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from clients.serializers import (
    ClientProfileSerializer,
    ClientLocationSerializer,
)
from clients.services.client_profile_service import ClientProfileService
from utils.permissions import IsClientOrAdmin, IsOwnerOrAdmin

User = get_user_model()


class ClientProfileViewSet(viewsets.ModelViewSet):
    """
    مدیریت پروفایل کلاینت‌ها (CRUD).

    ### متدهای اصلی:
    - **GET /clients/**: لیست پروفایل‌ها (ادمین: همه، کلاینت: فقط خودش)
    - **POST /clients/**: ایجاد پروفایل جدید (شناسهٔ کاربر الزامی است)
    - **GET /clients/{id}/**: جزئیات یک پروفایل
    - **PUT/PATCH /clients/{id}/**: ویرایش پروفایل
    - **DELETE /clients/{id}/**: حذف پروفایل

    ### اکشن‌های اختصاصی:
    - **POST /clients/set-location/**: ذخیرهٔ موقعیت مکانی کلاینت
      - Body: `{"lat": 35.6892, "lng": 51.3890}`
      - Response: `{"message": "...", "location": {"lat": ..., "lng": ...}}`

    - **GET/PATCH /clients/me/**: دریافت یا ویرایش پروفایل کاربر جاری
      - GET: اطلاعات کامل پروفایل
      - PATCH: ویرایش جزئی (فقط فیلدهای ارسالی)

    - **POST /clients/select-advertiser-type/**: انتخاب نوع فعالیت (حقیقی/حقوقی)
      - Body: `{"advertiser_type": "REAL"}`
      - Response: `{"message": "...", "kyc_step": "UPLOAD_DOCUMENTS"}`

    ### محدودیت‌ها:
    - فقط کاربران با نقش CLIENT و ادمین دسترسی دارند.
    - هر کاربر فقط پروفایل خود را می‌تواند ویرایش کند.
    """
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    def get_queryset(self):
        return ClientProfileService.get_queryset(self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # ========== Set Location ==========
    @action(detail=False, methods=['post'], url_path='set-location')
    def set_location(self, request):
        serializer = ClientLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data['lat']
        lng = serializer.validated_data['lng']

        profile = self.get_queryset().first()
        if not profile:
            return Response({"error": "پروفایلی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        result = ClientProfileService.set_location(profile, lat, lng)
        return Response(result)

    # ========== My Profile ==========
    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def my_profile(self, request):
        profile = self.get_queryset().first()
        if not profile:
            return Response({"error": "پروفایلی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        else:  # PATCH
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    # ========== Select Advertiser Type ==========
    @action(detail=False, methods=['post'], url_path='select-advertiser-type')
    def select_advertiser_type(self, request):
        profile = self.get_queryset().first()
        if not profile:
            return Response({"error": "پروفایلی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        adv_type = request.data.get('advertiser_type')
        try:
            result = ClientProfileService.select_advertiser_type(profile, adv_type)
            return Response(result)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)