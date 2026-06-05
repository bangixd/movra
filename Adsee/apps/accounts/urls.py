from django.urls import path, include
from .views import UserDetailAPIView, RequestOTPView, VerifyOTPView

urlpatterns = [
    path("auth/request-otp/", RequestOTPView.as_view(), name="request_otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path('user/', UserDetailAPIView.as_view(), name='user_detail'),
]