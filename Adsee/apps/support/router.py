from rest_framework.routers import DefaultRouter
from support.views import (
    AdminFAQCategoryViewSet,
    AdminFAQItemViewSet,
    AdminSupportContentViewSet,
    AdminTicketViewSet,
    AdminAppDownloadViewSet,
    SupportContentViewSet
)

router = DefaultRouter()
router.register(r'content', SupportContentViewSet, basename='support-content')
router.register(r'admin/faq-categories', AdminFAQCategoryViewSet, basename='admin-faq-category')
router.register(r'admin/faq-items', AdminFAQItemViewSet, basename='admin-faq-item')
router.register(r'admin/contents', AdminSupportContentViewSet, basename='admin-content')
router.register(r'admin/tickets', AdminTicketViewSet, basename='admin-ticket')
router.register(r'admin/downloads', AdminAppDownloadViewSet, basename='admin-app-download')
