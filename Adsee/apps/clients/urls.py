from django.urls import path, include
from clients.views import reverse_geocode,\
    ClientPeakHoursView, ClientReportSummaryView, BillboardComparisonView, ClientCampaignListView, ClientHomeView
from .router import router
urlpatterns =[
    path('home/', ClientHomeView.as_view(), name='client-home'),
    path('campaigns/', ClientCampaignListView.as_view(), name='client-campaign-list'),
    path('reports/summary/', ClientReportSummaryView.as_view(), name='report-summary'),
    path('reports/peak-hours/', ClientPeakHoursView.as_view(), name='report-peak-hours'),
    path('reports/billboard-comparison/', BillboardComparisonView.as_view(), name='report-billboard'),
    path('reverse-geocode/', reverse_geocode, name='reverse-geocode'),
]+ router.urls