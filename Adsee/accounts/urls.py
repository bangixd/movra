from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (UserDetailAPIView, RequestOTPView, VerifyOTPView, DriverProfileViewSet, ClientProfileViewSet,
                    DriverKycStatusView, DriverProfileKycAdminView, DriverDocumentUploadView)

router = DefaultRouter()
router.register(r'driver-profiles', DriverProfileViewSet, basename='driverprofile')
router.register(r'client-profiles', ClientProfileViewSet, basename='clientprofile')

urlpatterns = [
    path("auth/request-otp/", RequestOTPView.as_view(), name="request_otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),

    path('user/', UserDetailAPIView.as_view(), name='user_detail'),

    path('', include(router.urls)),

    # برای راننده
    path('kyc/driver/upload/', DriverDocumentUploadView.as_view(), name='driver-kyc-upload'),
    path('kyc/driver/status/', DriverKycStatusView.as_view(), name='driver-kyc-status'),

    # Endpoints برای ادمین
    path('admin/kyc/driver/review/<int:user_id>/', DriverProfileKycAdminView.as_view(), name='driver-kyc-admin-review'),
]