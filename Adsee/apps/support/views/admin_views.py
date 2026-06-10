from rest_framework import viewsets
from support.serializers import (
    SiteSettingSerializer,
    FAQCategoryWriteSerializer, FAQCategoryReadSerializer,
    FAQItemWriteSerializer, FAQItemReadSerializer,
    SupportContentSerializer,
    TicketAdminSerializer,
    AppDownloadLinkSerializer,
)
from support.services.support_admin_service import SupportAdminService
from utils.permissions import IsAdminUser


class AdminFAQCategoryViewSet(viewsets.ModelViewSet):
    """
    مدیریت دسته‌بندی‌های FAQ (ادمین).
    """
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return SupportAdminService.get_all_faq_categories()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return FAQCategoryReadSerializer
        return FAQCategoryWriteSerializer


class AdminFAQItemViewSet(viewsets.ModelViewSet):
    """
    مدیریت سوالات FAQ (ادمین).
    """
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return SupportAdminService.get_all_faq_items()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return FAQItemReadSerializer
        return FAQItemWriteSerializer


class AdminSupportContentViewSet(viewsets.ModelViewSet):
    """
    مدیریت محتوای پشتیبانی (ادمین).
    """
    serializer_class = SupportContentSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return SupportAdminService.get_all_support_content()


class AdminTicketViewSet(viewsets.ModelViewSet):
    """
    مدیریت تیکت‌ها (ادمین).
    """
    serializer_class = TicketAdminSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return SupportAdminService.get_all_tickets()


class AdminAppDownloadViewSet(viewsets.ModelViewSet):
    """
    مدیریت لینک‌های دانلود (ادمین).
    """
    serializer_class = AppDownloadLinkSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return SupportAdminService.get_all_app_downloads()