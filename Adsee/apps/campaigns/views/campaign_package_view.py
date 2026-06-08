from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from campaigns.models import CampaignPackage
from campaigns.serializers import CampaignPackageSerializer


class CampaignPackageViewSet(ModelViewSet):
    """
    مدیریت پکیج‌های کمپین (فقط ادمین).

    ### متدهای اصلی:
    - **GET /campaigns/packages/**: لیست پکیج‌های فعال (همهٔ کاربران لاگین‌شده)
    - **POST /campaigns/packages/**: ایجاد پکیج جدید (فقط ادمین)
    - **GET /campaigns/packages/{id}/**: جزئیات
    - **PUT/PATCH /campaigns/packages/{id}/**: ویرایش (فقط ادمین)
    - **DELETE /campaigns/packages/{id}/**: حذف (فقط ادمین)
    """
    queryset = CampaignPackage.objects.filter(is_active=True)
    serializer_class = CampaignPackageSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]