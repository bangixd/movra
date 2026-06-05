from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupportContentViewSet, SiteSettingView, TicketCreateView, TicketListView, FAQListView,\
    AppDownloadListView
from .admin_views import (
    AdminSiteSettingViewSet,
    AdminFAQCategoryViewSet,
    AdminFAQItemViewSet,
    AdminSupportContentViewSet,
    AdminTicketViewSet,
    AdminAppDownloadViewSet
)

router = DefaultRouter()
router.register(r'admin/site-settings', AdminSiteSettingViewSet, basename='admin-site-setting')
router.register(r'admin/faq-categories', AdminFAQCategoryViewSet, basename='admin-faq-category')
router.register(r'admin/faq-items', AdminFAQItemViewSet, basename='admin-faq-item')
router.register(r'admin/contents', AdminSupportContentViewSet, basename='admin-content')
router.register(r'admin/tickets', AdminTicketViewSet, basename='admin-ticket')
router.register(r'admin/downloads', AdminAppDownloadViewSet, basename='admin-app-download')

urlpatterns = [
    # عمومی
    path('content/', SupportContentViewSet.as_view({'get': 'list'}), name='support-content'),
    path('about/', SiteSettingView.as_view(), name='site-about'),
    path('faq/', FAQListView.as_view(), name='faq-list'),
    path('tickets/', TicketCreateView.as_view(), name='ticket-create'),
    path('tickets/list/', TicketListView.as_view(), name='ticket-list'),
    path('downloads/', AppDownloadListView.as_view(), name='app-downloads'),
    # ادمین (نیاز به توکن ادمین)
    path('', include(router.urls)),
]