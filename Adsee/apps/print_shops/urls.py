from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import PrintShopProfileViewSet, AssignedDesignsListView, UpdateDesignPrintStatusView

router = DefaultRouter()
router.register(r'profile', PrintShopProfileViewSet, basename='print_shops')
urlpatterns = router.urls + [
    path('designs/', AssignedDesignsListView.as_view(), name='assigned-designs'),
    path('designs/<int:design_id>/status/', UpdateDesignPrintStatusView.as_view(), name='design-status-update'),

]