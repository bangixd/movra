from rest_framework.routers import DefaultRouter
from .views import (
    CampaignViewSet,
    CampaignGoalViewSet,
    BannerTypeViewSet,
    TemplateViewSet,
    CampaignPricingRuleViewSet,
    CampaignPackageViewSet
)

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'goals', CampaignGoalViewSet, basename='goal')
router.register(r'banner-types', BannerTypeViewSet, basename='banner-type')
router.register(r'templates', TemplateViewSet, basename='template')
router.register(r'pricing-rules', CampaignPricingRuleViewSet, basename='pricing-rules')
router.register(r'packages', CampaignPackageViewSet, basename='campaign-packages')