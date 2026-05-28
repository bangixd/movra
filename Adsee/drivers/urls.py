from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (DriverProfileViewSet, DriverDocumentViewSet, apply_referral_code)

router = DefaultRouter()
router.register(r'profile', DriverProfileViewSet, basename='driver-profile')
router.register(r'documents', DriverDocumentViewSet, basename='driver-document')
urlpatterns = [
    path('apply-referral/', apply_referral_code, name='apply-referral'),
] + router.urls