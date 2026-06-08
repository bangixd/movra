from rest_framework.viewsets import ModelViewSet
from campaigns.serializers import (
    CampaignDesignSerializer,
    CampaignAreaDetailSerializer,
    CampaignAreaCreateSerializer,
    CampaignSettingSerializer,
    CampaignInvoiceSerializer,
    CampaignSerializer
)
from campaigns.services import (
    CampaignAreaService,
    CampaignDesignService,
    CampaignSettingService,
    InvoiceService,
    PaymentService,
    CampaignService
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from utils.permissions import IsClientUser, IsOwnerOrAdmin
from campaigns.models import CampaignDesign, CampaignArea, CampaignSetting, CampaignInvoice


class CampaignViewSet(ModelViewSet):
    """
    مدیریت کمپین‌ها (CRUD).

    ### متدهای اصلی:
    - **GET /campaigns/**: لیست کمپین‌ها (ادمین: همه، کلاینت: فقط کمپین‌های خودش)
    - **POST /campaigns/**: ایجاد کمپین جدید
      - Body: `{"slogan": "...", "brand_name": 1, "start_date": "...", "end_date": "...", ...}`
    - **GET /campaigns/{id}/**: جزئیات یک کمپین
    - **PUT/PATCH /campaigns/{id}/**: ویرایش کمپین
    - **DELETE /campaigns/{id}/**: حذف منطقی کمپین (is_deleted=True)

    ### عملیات‌های خاص کمپین:
    - **POST /campaigns/{id}/add-vehicles/**: افزایش تعداد خودرو
      - Body: `{"count": 3}`
      - Response: `{"payment_url": "...", "invoice_id": 1, "extra_amount": 150000, "total": 163500}`

    - **POST /campaigns/{id}/extend/**: تمدید مدت کمپین
      - Body: `{"days": 5}`
      - Response: `{"payment_url": "...", "invoice_id": 2, "extra_amount": 500000, "total": 545000}`

    - **POST /campaigns/{id}/change-design/**: تغییر طراحی (بنر)
      - Body: `{"design_type": "CUSTOM_DESIGN", ...}`
      - Response: `{"payment_url": "...", "invoice_id": 3, "extra_amount": 150000, "total": 163500}`
      - اگر مابه‌التفاوت صفر باشد: `{"message": "تغییرات با موفقیت اعمال شد", "paid": false}`

    - **POST /campaigns/{id}/pause/**: توقف یا ادامهٔ کمپین (Toggle)
      - Response: `{"status": "PAUSED"}` یا `{"status": "ACTIVE"}`

    ### مدیریت طراحی:
    - **GET /campaigns/{id}/design/**: دریافت طراحی فعلی کمپین
    - **PUT/PATCH /campaigns/{id}/design/**: ایجاد یا ویرایش طراحی

    ### مدیریت محدوده:
    - **GET /campaigns/{id}/area/**: دریافت محدودهٔ جغرافیایی
    - **PUT/PATCH /campaigns/{id}/area/**: ایجاد یا ویرایش محدوده

    ### مدیریت تنظیمات:
    - **GET /campaigns/{id}/setting/**: دریافت تنظیمات کمپین
    - **PUT/PATCH /campaigns/{id}/setting/**: ایجاد یا ویرایش تنظیمات

    ### مدیریت فاکتور:
    - **GET /campaigns/{id}/invoice/**: دریافت فاکتور کمپین
    - **POST /campaigns/{id}/invoice/pay/**: شروع فرآیند پرداخت
      - Response: `{"payment_url": "...", "invoice_id": 5}`

    ### محدودیت‌ها:
    - فقط کاربران با نقش CLIENT و ادمین دسترسی دارند.
    - هر کلاینت فقط کمپین‌های خود را می‌تواند مدیریت کند.
    """
    permission_classes = [IsClientUser,]
    serializer_class = CampaignSerializer

    def get_queryset(self):
        return CampaignService.get_queryset(self.request.user)

    def perform_create(self, serializer):
        # فراخوانی سرویس برای ایجاد کمپین
        campaign = CampaignService.create_campaign(
            self.request.user,
            serializer.validated_data
        )
        serializer.instance = campaign

    # ========== افزودن خودرو ==========
    @action(detail=True, methods=['post'], url_path='add-vehicles')
    def add_vehicles(self, request, pk=None):
        campaign = self.get_object()
        additional_vehicles = request.data.get('count')
        if not additional_vehicles:
            return Response({"error": "تعداد خودروی اضافی الزامی است"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            additional_vehicles = int(additional_vehicles)
            if additional_vehicles <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "تعداد باید یک عدد صحیح مثبت باشد"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = CampaignService.add_vehicles(campaign, additional_vehicles)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ========== تمدید کمپین ==========
    @action(detail=True, methods=['post'], url_path='extend')
    def extend(self, request, pk=None):
        campaign = self.get_object()
        additional_days = request.data.get('days')
        if not additional_days:
            return Response({"error": "تعداد روز تمدید الزامی است"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            additional_days = int(additional_days)
            if additional_days <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "تعداد روز باید یک عدد صحیح مثبت باشد"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = CampaignService.extend(campaign, additional_days)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ========== تغییر طراحی ==========
    @action(detail=True, methods=['post'], url_path='change-design')
    def change_design(self, request, pk=None):
        campaign = self.get_object()
        design_serializer = CampaignDesignSerializer(data=request.data)
        if not design_serializer.is_valid():
            return Response(design_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        new_design_data = design_serializer.validated_data
        try:
            result = CampaignService.change_design(campaign, new_design_data)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ========== توقف/ادامه کمپین ==========
    @action(detail=True, methods=['post'], url_path='pause')
    def pause(self, request, pk=None):
        campaign = self.get_object()
        try:
            result = CampaignService.toggle_pause(campaign)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ========== طراحی کمپین ==========
    @action(detail=True, methods=['get'], url_path='design')
    def design_detail(self, request, pk=None):
        campaign = self.get_object()
        try:
            design = campaign.design
        except CampaignDesign.DoesNotExist:
            return Response({"detail": "طراحی وجود ندارد."}, status=404)
        serializer = CampaignDesignSerializer(design)
        return Response(serializer.data)

    @design_detail.mapping.put
    @design_detail.mapping.patch
    def design_update(self, request, pk=None):
        campaign = self.get_object()
        try:
            design = campaign.design
        except CampaignDesign.DoesNotExist:
            design = CampaignDesign(campaign=campaign)
        serializer = CampaignDesignSerializer(design, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ========== محدوده کمپین ==========
    @action(detail=True, methods=['get'], url_path='area')
    def area_detail(self, request, pk=None):
        campaign = self.get_object()
        try:
            area = campaign.area
        except CampaignArea.DoesNotExist:
            return Response({"detail": "محدوده‌ای تعریف نشده."}, status=404)
        serializer = CampaignAreaDetailSerializer(area)
        return Response(serializer.data)

    @area_detail.mapping.put
    @area_detail.mapping.patch
    def area_update(self, request, pk=None):
        campaign = self.get_object()
        try:
            area = campaign.area
        except CampaignArea.DoesNotExist:
            area = CampaignArea(campaign=campaign)
        serializer = CampaignAreaCreateSerializer(area, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        CampaignAreaService.validate_campaign_ownership(request.user, campaign)
        serializer.save()
        return Response(CampaignAreaDetailSerializer(area).data)

    # ========== تنظیمات کمپین ==========
    @action(detail=True, methods=['get'], url_path='setting')
    def setting_detail(self, request, pk=None):
        campaign = self.get_object()
        try:
            setting = campaign.setting
        except CampaignSetting.DoesNotExist:
            return Response({"detail": "تنظیماتی یافت نشد."}, status=404)
        serializer = CampaignSettingSerializer(setting)
        return Response(serializer.data)

    @setting_detail.mapping.put
    @setting_detail.mapping.patch
    def setting_update(self, request, pk=None):
        campaign = self.get_object()
        try:
            setting = campaign.setting
        except CampaignSetting.DoesNotExist:
            setting = CampaignSetting(campaign=campaign)
        serializer = CampaignSettingSerializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ========== فاکتور کمپین ==========
    @action(detail=True, methods=['get'], url_path='invoice')
    def invoice_detail(self, request, pk=None):
        campaign = self.get_object()
        try:
            invoice = campaign.invoice
        except CampaignInvoice.DoesNotExist:
            return Response({"detail": "فاکتوری صادر نشده."}, status=404)
        serializer = CampaignInvoiceSerializer(invoice)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='invoice/pay')
    def invoice_pay(self, request, pk=None):
        campaign = self.get_object()
        try:
            invoice = PaymentService.create_or_get_invoice(campaign)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = PaymentService.initiate_payment(invoice, campaign, request.user.phone)
            return Response(result, status=status.HTTP_200_OK)
        except ConnectionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)