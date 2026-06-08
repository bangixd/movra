from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from campaigns.models import CampaignPricingRule
from campaigns.serializers import CampaignPricingRuleSerializer


class CampaignPricingRuleViewSet(ModelViewSet):
    """
    مدیریت قوانین قیمت‌گذاری
    - GET: همهٔ کاربران لاگین‌شده
    - POST/PUT/PATCH/DELETE: فقط ادمین
    """
    queryset = CampaignPricingRule.objects.filter(is_active=True)
    serializer_class = CampaignPricingRuleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]