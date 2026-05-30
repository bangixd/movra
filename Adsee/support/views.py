from rest_framework import viewsets, permissions
from rest_framework.generics import RetrieveAPIView, CreateAPIView, ListAPIView
from .models import SupportContent, SiteSetting, Ticket, FAQCategory
from .serializers import SupportContentSerializer, SiteSettingSerializer, TicketListSerializer, TicketCreateSerializer,\
    FAQCategorySerializer

class SupportContentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SupportContentSerializer
    permission_classes = [permissions.AllowAny]  # صفحه عمومی، نیاز به احراز هویت ندارد

    def get_queryset(self):
        queryset = SupportContent.objects.filter(is_active=True)
        content_type = self.request.query_params.get('type', None)
        if content_type:
            queryset = queryset.filter(type=content_type.upper())
        return queryset


class SiteSettingView(RetrieveAPIView):
    permission_classes = [permissions.AllowAny]  # صفحه عمومی
    serializer_class = SiteSettingSerializer

    def get_object(self):
        # همیشه اولین تنظیمات فعال را برگردان (می‌توان بر اساس معیار دیگری انتخاب کرد)
        return SiteSetting.objects.filter(is_active=True).first()

class TicketCreateView(CreateAPIView):
    serializer_class = TicketCreateSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

class TicketListView(ListAPIView):
    serializer_class = TicketListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)


class FAQListView(ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = FAQCategorySerializer
    queryset = FAQCategory.objects.filter(is_active=True).prefetch_related('faqs')