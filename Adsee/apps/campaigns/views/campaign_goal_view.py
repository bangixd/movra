from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from campaigns.models import CampaignGoal
from campaigns.serializers import CampaignGoalSerializer


class CampaignGoalViewSet(ModelViewSet):
    """
    مدیریت اهداف کمپین (فقط ادمین).

    ### متدهای اصلی:
    - **GET /campaigns/goals/**: لیست اهداف فعال (همهٔ کاربران لاگین‌شده)
    - **POST /campaigns/goals/**: ایجاد هدف جدید (فقط ادمین)
      - Body: `{"title": "افزایش فروش", "is_active": true}`
    - **GET /campaigns/goals/{id}/**: جزئیات
    - **PUT/PATCH /campaigns/goals/{id}/**: ویرایش (فقط ادمین)
    - **DELETE /campaigns/goals/{id}/**: حذف (فقط ادمین)
    """
    queryset = CampaignGoal.objects.filter(is_active=True)
    serializer_class = CampaignGoalSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]