from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from campaigns.models import BannerType
from campaigns.serializers import BannerTypeSerializer


class BannerTypeViewSet(ModelViewSet):
    """
    مدیریت انواع بنر (فقط ادمین).

    ### متدهای اصلی:
    - **GET /campaigns/banner-types/**: لیست انواع بنر (همهٔ کاربران لاگین‌شده)
    - **POST /campaigns/banner-types/**: ایجاد نوع بنر جدید (فقط ادمین)
      - Body: `{"name": "بنر پشت", "is_active": true}`
    - **GET /campaigns/banner-types/{id}/**: جزئیات
    - **PUT/PATCH /campaigns/banner-types/{id}/**: ویرایش (فقط ادمین)
    - **DELETE /campaigns/banner-types/{id}/**: حذف (فقط ادمین)
    """
    queryset = BannerType.objects.filter(is_active=True)
    serializer_class = BannerTypeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]