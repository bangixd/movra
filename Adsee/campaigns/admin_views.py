from rest_framework import viewsets
from .models import CampaignGoal, BannerType, Template, CampaignPricingRule, CampaignPackage
from .serializers import CampaignGoalSerializer, BannerTypeSerializer, TemplateSerializer, PricingRuleAdminSerializer,\
    CampaignPackageSerializer
from permissions import IsAdminUser

class AdminCampaignGoalViewSet(viewsets.ModelViewSet):
    queryset = CampaignGoal.objects.all()
    serializer_class = CampaignGoalSerializer
    permission_classes = [IsAdminUser]

class AdminBannerTypeViewSet(viewsets.ModelViewSet):
    queryset = BannerType.objects.all()
    serializer_class = BannerTypeSerializer
    permission_classes = [IsAdminUser]

class AdminTemplateViewSet(viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [IsAdminUser]

class AdminPricingRuleViewSet(viewsets.ModelViewSet):
    """
        DESIGN_BASE_COST

        DESIGN_CUSTOM_COST

        DESIGN_UPLOAD_COST

        AREA_CIRCLE_COST_PER_KM

        AREA_SUGGESTED_ROUTE_COST_PER_KM

        AREA_FREE_COST_MULTIPLIER

        DRIVER_COST_PER_DAY

        BILLBOARD_DAILY_IMPRESSIONS
        اینها کلید های اجباری و پایه هستند که ادمین باید انها را مقدار دهی کند
        """
    queryset = CampaignPricingRule.objects.all()
    serializer_class = PricingRuleAdminSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        # فقط قوانین مربوط به هزینه‌های کمپین (می‌توان همه را برگرداند)
        return super().get_queryset()

class AdminCampaignPackageViewSet(viewsets.ModelViewSet):
    queryset = CampaignPackage.objects.all()
    serializer_class = CampaignPackageSerializer
    permission_classes = [IsAdminUser]