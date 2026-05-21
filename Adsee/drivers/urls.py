from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (DriverProfileViewSet, DriverDocumentViewSet)

router = DefaultRouter()
router.register(r'profile', DriverProfileViewSet, basename='driver-profile')
router.register(r'documents', DriverDocumentViewSet, basename='driver-document')
urlpatterns = router.urls