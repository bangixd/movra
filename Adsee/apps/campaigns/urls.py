from django.urls import path
from .views import CampaignBannerImagesView, \
    PaymentRequestView, PaymentVerifyView, \
    CampaignAnalysisListView, CampaignAnalysisCSVView, \
    campaign_cost
from .routers import router

urlpatterns = router.urls + [
    path('payments/request/', PaymentRequestView.as_view(), name='payment-request'),
    path('payments/verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('<int:campaign_id>/banner-images/', CampaignBannerImagesView.as_view(), name='campaign-banner-images'),
    path('<int:campaign_id>/cost/', campaign_cost, name='campaign-cost'),
    path('<int:campaign_id>/analysis/', CampaignAnalysisListView.as_view(), name='campaign-analysis'),
    path('<int:campaign_id>/analysis/csv/', CampaignAnalysisCSVView.as_view(), name='campaign-analysis-csv'),

]