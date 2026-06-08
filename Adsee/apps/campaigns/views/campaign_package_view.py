from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from campaigns.models import CampaignPackage
from campaigns.serializers import CampaignPackageSerializer


class CampaignPackageViewSet(ModelViewSet):
    """
    مدیریت پکیج‌های کمپین
    - GET: همهٔ کاربران لاگین‌شده
    - POST/PUT/PATCH/DELETE: فقط ادمین
    """
    queryset = CampaignPackage.objects.filter(is_active=True)
    serializer_class = CampaignPackageSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]