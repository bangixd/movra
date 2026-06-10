from rest_framework import viewsets, mixins
from support.serializers import SupportContentSerializer, AppDownloadLinkSerializer, FAQCategorySerializer
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework import permissions
from support.serializers import SiteSettingSerializer
from support.services.support_service import SupportService
from utils.permissions import IsAdminUser


class SiteSettingViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    """
    مدیریت تنظیمات سایت (Singleton).

    - **GET /support/site-settings/** – دریافت تنظیمات (عمومی، بدون احراز هویت)
    - **PUT /support/site-settings/** – ویرایش کامل (فقط ادمین)
    - **PATCH /support/site-settings/** – ویرایش جزئی (فقط ادمین)

    همیشه اولین (و تنها) رکورد فعال را برمی‌گرداند.
    """
    serializer_class = SiteSettingSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsAdminUser()]
        return [permissions.AllowAny()]

    def get_object(self):
        return SupportService.get_site_setting()


class SupportContentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    محتوای پشتیبانی (تماس با ما، درباره ما، سوالات متداول).

    ### متدهای اصلی:
    - **GET /support/**: لیست همهٔ محتوای فعال
      - پارامتر اختیاری Query: `?type=CONTACT` (فیلتر بر اساس نوع)
    - **GET /support/{id}/**: جزئیات یک محتوا

    ### دسترسی:
    - عمومی (بدون نیاز به احراز هویت)
    """
    serializer_class = SupportContentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        content_type = self.request.query_params.get('type', None)
        return SupportService.get_active_content(content_type)


class FAQListView(ListAPIView):
    """
    لیست سوالات متداول (دسته‌بندی‌شده).

    ### GET /support/faq/
    برگرداندن همهٔ دسته‌بندی‌های فعال FAQ به همراه سوالات.

    ### نمونه پاسخ:
    ```json
    [
        {
            "id": 1,
            "title": "ثبت‌نام",
            "faqs": [
                {"id": 1, "question": "چگونه ثبت‌نام کنم؟", "answer": "..."},
                ...
            ]
        },
        ...
    ]
    عمومی (بدون نیاز به احراز هویت)
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = FAQCategorySerializer

    def get_queryset(self):
        return SupportService.get_faq_categories()

class AppDownloadListView(ListAPIView):
    """
لینک‌های دانلود اپلیکیشن.

    GET /support/app-downloads/
برگرداندن لینک‌های فعال دانلود اپلیکیشن.
    [
        {
            "id": 1,
            "platform": "ANDROID",
            "title": "دانلود از کافه بازار",
            "url": "https://cafebazaar.ir/app/...",
            "icon": "https://movra.ir/media/icons/bazaar.png"
        },
        ...
    ]
    عمومی (بدون نیاز به احراز هویت)
    """

    serializer_class = AppDownloadLinkSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return SupportService.get_app_download_links()