from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import CampaignDesignViewSet, CampaignViewSet, CampaignSettingViewSet,\
    CampaignAreaViewSet,\
    CampaignPricingRuleViewSet, CampaignInvoiceViewSet, PaymentRequestView, PaymentVerifyView, \
    CampaignAnalysisListView, CampaignAnalysisCSVView, BannerTypeListView, CampaignGoalListView, TemplateListView, \
    campaign_cost, CampaignPackageListView
from .admin_views import AdminCampaignGoalViewSet, AdminBannerTypeViewSet, AdminTemplateViewSet, \
    AdminPricingRuleViewSet, AdminCampaignPackageViewSet


router = DefaultRouter()
router.register(r'', CampaignViewSet, basename='campaign')
router.register(r'campaign-setting', CampaignSettingViewSet, basename='campaign-setting')
router.register(r'campaign-designs', CampaignDesignViewSet, basename='campaign-designs')
router.register(r"campaign-areas", CampaignAreaViewSet, basename="campaign-area")
router.register(r"pricing-rules", CampaignPricingRuleViewSet, basename="pricing-rules")
router.register(r"campaign-invoices", CampaignInvoiceViewSet, basename="campaign-invoices")
router.register(r'admin/goals', AdminCampaignGoalViewSet, basename='admin-goal')
router.register(r'admin/banner-types', AdminBannerTypeViewSet, basename='admin-banner-type')
router.register(r'admin/templates', AdminTemplateViewSet, basename='admin-template')
router.register(r'admin/pricing-rules', AdminPricingRuleViewSet, basename='admin-pricing-rules')
router.register(r'admin/campaign-packages', AdminCampaignPackageViewSet, basename='admin-campaign-packages')


urlpatterns = router.urls + [
    path('payments/request/', PaymentRequestView.as_view(), name='payment-request'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('goals/', CampaignGoalListView.as_view(), name='goal-list'),
    path('banner-types/', BannerTypeListView.as_view(), name='banner-type-list'),
    path('templates/', TemplateListView.as_view(), name='template-list'),
    path('packages/', CampaignPackageListView.as_view(), name='package-list'),
    path('<int:campaign_id>/cost/', campaign_cost, name='campaign-cost'),
    path('<int:campaign_id>/analysis/', CampaignAnalysisListView.as_view(), name='campaign-analysis'),
    path('<int:campaign_id>/analysis/csv/', CampaignAnalysisCSVView.as_view(), name='campaign-analysis-csv'),

]