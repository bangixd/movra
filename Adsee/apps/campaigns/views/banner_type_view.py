from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from campaigns.models import BannerType
from campaigns.serializers import BannerTypeSerializer


class BannerTypeViewSet(ModelViewSet):
    """
    مدیریت انواع بنر
    - GET: همهٔ کاربران لاگین‌شده
    - POST/PUT/PATCH/DELETE: فقط ادمین
    """
    queryset = BannerType.objects.filter(is_active=True)
    serializer_class = BannerTypeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]