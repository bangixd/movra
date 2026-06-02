from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientProfileViewSet, ClientDocumentViewSet, reverse_geocode,\
    ClientPeakHoursView, ClientReportSummaryView, BillboardComparisonView, ClientCampaignListView

router = DefaultRouter()
router.register(r'documents', ClientDocumentViewSet, basename='client-document')
router.register(r'', ClientProfileViewSet, basename='client-profile')
urlpatterns =[
    path('campaigns/', ClientCampaignListView.as_view(), name='client-campaign-list'),
    path('reports/summary/', ClientReportSummaryView.as_view(), name='report-summary'),
    path('reports/peak-hours/', ClientPeakHoursView.as_view(), name='report-peak-hours'),
    path('reports/billboard-comparison/', BillboardComparisonView.as_view(), name='report-billboard'),
    path('reverse-geocode/', reverse_geocode, name='reverse-geocode'),
]+ router.urls