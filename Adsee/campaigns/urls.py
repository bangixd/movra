from rest_framework.routers import DefaultRouter
from .views import CampaignDesignViewSet, CampaignViewSet, CampaignSettingViewSet, TemplateViewSet,\
    CampaignAreaViewSet,\
    CampaignPricingRuleViewSet, CampaignCostViewSet, CampaignInvoiceViewSet

router = DefaultRouter()
router.register(r'campaign', CampaignViewSet, basename='campaign')
router.register(r'campaign-setting', CampaignSettingViewSet, basename='campaign-setting')
router.register(r'templates', TemplateViewSet, basename='templates')
router.register(r'campaign-designs', CampaignDesignViewSet, basename='campaign-designs')
router.register(r"campaign-areas", CampaignAreaViewSet, basename="campaign-area")
router.register(r"pricing-rules", CampaignPricingRuleViewSet, basename="pricing-rules")
router.register(r"campaign-costs", CampaignCostViewSet, basename="campaign-costs")
router.register(r"campaign-invoices", CampaignInvoiceViewSet, basename="campaign-invoices")


urlpatterns = router.urls
