from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import CampaignDesignViewSet, CampaignViewSet, CampaignSettingViewSet, TemplateViewSet,\
    CampaignAreaViewSet,\
    CampaignPricingRuleViewSet, CampaignCostViewSet, CampaignInvoiceViewSet, PaymentRequestView, PaymentVerifyView, \
    CampaignAnalysisListView, CampaignAnalysisCSVView

router = DefaultRouter()
router.register(r'', CampaignViewSet, basename='campaign')
router.register(r'campaign-setting', CampaignSettingViewSet, basename='campaign-setting')
router.register(r'templates', TemplateViewSet, basename='templates')
router.register(r'campaign-designs', CampaignDesignViewSet, basename='campaign-designs')
router.register(r"campaign-areas", CampaignAreaViewSet, basename="campaign-area")
router.register(r"pricing-rules", CampaignPricingRuleViewSet, basename="pricing-rules")
router.register(r"campaign-costs", CampaignCostViewSet, basename="campaign-costs")
router.register(r"campaign-invoices", CampaignInvoiceViewSet, basename="campaign-invoices")


urlpatterns = router.urls + [
    path('payments/request/', PaymentRequestView.as_view(), name='payment-request'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('<int:campaign_id>/analysis/', CampaignAnalysisListView.as_view(), name='campaign-analysis'),
    path('<int:campaign_id>/analysis/csv/', CampaignAnalysisCSVView.as_view(), name='campaign-analysis-csv'),

]