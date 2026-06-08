from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from campaigns.models import CampaignGoal
from campaigns.serializers import CampaignGoalSerializer


class CampaignGoalViewSet(ModelViewSet):
    """
    مدیریت اهداف کمپین
    - GET: همهٔ کاربران لاگین‌شده
    - POST/PUT/PATCH/DELETE: فقط ادمین
    """
    queryset = CampaignGoal.objects.filter(is_active=True)
    serializer_class = CampaignGoalSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]