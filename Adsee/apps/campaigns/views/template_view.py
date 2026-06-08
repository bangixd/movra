from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from campaigns.models import Template
from campaigns.serializers import TemplateSerializer


class TemplateViewSet(ModelViewSet):
    """
    مدیریت قالب‌های طراحی
    - GET: همهٔ کاربران لاگین‌شده
    - POST/PUT/PATCH/DELETE: فقط ادمین
    """
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]