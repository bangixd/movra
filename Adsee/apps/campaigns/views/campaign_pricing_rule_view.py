from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from campaigns.models import CampaignPricingRule
from campaigns.serializers import CampaignPricingRuleSerializer


class CampaignPricingRuleViewSet(ModelViewSet):
    """
    مدیریت قوانین قیمت‌گذاری (فقط ادمین).

    ### متدهای اصلی:
    - **GET /campaigns/pricing-rules/**: لیست قوانین (همهٔ کاربران لاگین‌شده)
    - **POST /campaigns/pricing-rules/**: ایجاد قانون جدید (فقط ادمین)
      - Body: `{"key": "DRIVER_COST_PER_DAY", "title": "...", "value_type": "DECIMAL", "decimal_value": 200000}`
    - **GET /campaigns/pricing-rules/{id}/**: جزئیات یک قانون
    - **PUT/PATCH /campaigns/pricing-rules/{id}/**: ویرایش قانون (فقط ادمین)
    - **DELETE /campaigns/pricing-rules/{id}/**: حذف قانون (فقط ادمین)

    ### نکات:
    - برای GET نیاز به احراز هویت است (هر کاربر لاگین‌شده).
    - برای POST/PUT/DELETE فقط ادمین دسترسی دارد.
    - قوانین با `is_active=True` فیلتر می‌شوند.
    """
    queryset = CampaignPricingRule.objects.filter(is_active=True)
    serializer_class = CampaignPricingRuleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]