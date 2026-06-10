from django.urls import path
from .views import SupportContentViewSet, TicketCreateView, TicketListView, FAQListView,\
    AppDownloadListView, SiteSettingViewSet
from .router import router


urlpatterns = router.urls + [
    path('site-settings/', SiteSettingViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update'
    }), name='site-settings'),
    # عمومی
    path('content/', SupportContentViewSet.as_view({'get': 'list'}), name='support-content'),
    path('faq/', FAQListView.as_view(), name='faq-list'),
    path('tickets/', TicketCreateView.as_view(), name='ticket-create'),
    path('tickets/mine/', TicketListView.as_view(), name='ticket-list'),
    path('app-downloads/', AppDownloadListView.as_view(), name='app-downloads'),
]