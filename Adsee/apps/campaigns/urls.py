from django.urls import path
from .views import CampaignBannerImagesView, \
    PaymentRequestView, PaymentVerifyView, \
    CampaignAnalysisListView, CampaignAnalysisCSVView, \
    campaign_cost
#CampaignPauseView,  CampaignChangeDesignView, CampaignExtendView, CampaignAddVehiclesView, CampaignPricingRuleViewSet,
# BannerTypeViewSet, CampaignGoalViewSet, TemplateViewSet,  CampaignPackageListView
from .routers import router

urlpatterns = router.urls + [
    path('payments/request/', PaymentRequestView.as_view(), name='payment-request'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    # path('goals/', CampaignGoalViewSet.as_view(), name='goal-list'),
    # path('banner-types/', BannerTypeListView.as_view(), name='banner-type-list'),
    # path('templates/', TemplateListView.as_view(), name='template-list'),
    # path('packages/', CampaignPackageListView.as_view(), name='package-list'),
    #path('<int:campaign_id>/change-design/', CampaignChangeDesignView.as_view(), name='campaign-change-design'),
    #path('<int:campaign_id>/add-vehicles/', CampaignAddVehiclesView.as_view(), name='campaign-add-vehicles'),
    #path('<int:campaign_id>/extend/', CampaignExtendView.as_view(), name='campaign-extend'),
    path('<int:campaign_id>/banner-images/', CampaignBannerImagesView.as_view(), name='campaign-banner-images'),
    #path('<int:campaign_id>/pause/', CampaignPauseView.as_view(), name='campaign-pause'),
    path('<int:campaign_id>/cost/', campaign_cost, name='campaign-cost'),
    path('<int:campaign_id>/analysis/', CampaignAnalysisListView.as_view(), name='campaign-analysis'),
    path('<int:campaign_id>/analysis/csv/', CampaignAnalysisCSVView.as_view(), name='campaign-analysis-csv'),

]