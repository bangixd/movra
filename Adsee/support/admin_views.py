from rest_framework import viewsets, permissions
from .models import SiteSetting, FAQCategory, FAQItem, SupportContent, Ticket, AppDownloadLink
from .serializers import (
    SiteSettingSerializer,
    FAQCategoryWriteSerializer, FAQCategoryReadSerializer,
    FAQItemWriteSerializer, FAQItemReadSerializer,
    SupportContentSerializer,
    TicketAdminSerializer,
    AppDownloadLinkSerializer,
)
from permissions import IsAdminUser

class AdminAppDownloadViewSet(viewsets.ModelViewSet):
    queryset = AppDownloadLink.objects.all()
    serializer_class = AppDownloadLinkSerializer
    permission_classes = [IsAdminUser]

class AdminSiteSettingViewSet(viewsets.ModelViewSet):
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [IsAdminUser]

    def get_object(self):
        # همیشه اولین (و تنها) رکورد را برگردان
        return SiteSetting.objects.first()

class AdminFAQCategoryViewSet(viewsets.ModelViewSet):
    queryset = FAQCategory.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return FAQCategoryReadSerializer
        return FAQCategoryWriteSerializer

class AdminFAQItemViewSet(viewsets.ModelViewSet):
    queryset = FAQItem.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return FAQItemReadSerializer
        return FAQItemWriteSerializer

class AdminSupportContentViewSet(viewsets.ModelViewSet):
    queryset = SupportContent.objects.all()
    serializer_class = SupportContentSerializer
    permission_classes = [IsAdminUser]

class AdminTicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketAdminSerializer
    permission_classes = [IsAdminUser]