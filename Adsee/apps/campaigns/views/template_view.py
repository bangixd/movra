from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from campaigns.models import Template
from campaigns.serializers import TemplateSerializer


class TemplateViewSet(ModelViewSet):
    """
    مدیریت قالب‌های طراحی (فقط ادمین).

    ### متدهای اصلی:
    - **GET /campaigns/templates/**: لیست قالب‌ها (همهٔ کاربران لاگین‌شده)
    - **POST /campaigns/templates/**: ایجاد قالب جدید (فقط ادمین)
      - Body: `{"name": "قالب شماره ۱", "variant": "template-1", "preview_image": ...}`
    - **GET /campaigns/templates/{id}/**: جزئیات یک قالب
    - **PUT/PATCH /campaigns/templates/{id}/**: ویرایش قالب (فقط ادمین)
    - **DELETE /campaigns/templates/{id}/**: حذف قالب (فقط ادمین)

    ### نکات:
    - برای GET نیاز به احراز هویت است.
    - برای POST/PUT/DELETE فقط ادمین دسترسی دارد.
    """
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]