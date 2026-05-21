from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (DriverProfileViewSet,
                    DriverKycStatusView, DriverProfileKycAdminView, DriverDocumentUploadView)

router = DefaultRouter()
router.register(r'driver-profiles', DriverProfileViewSet, basename='driverprofile')

urlpatterns = [
    path('', include(router.urls)),

    # برای راننده
    path('kyc/driver/upload/', DriverDocumentUploadView.as_view(), name='driver-kyc-upload'),
    path('kyc/driver/status/', DriverKycStatusView.as_view(), name='driver-kyc-status'),

    # Endpoints برای ادمین
    path('admin/kyc/driver/review/<int:user_id>/', DriverProfileKycAdminView.as_view(), name='driver-kyc-admin-review'),
]