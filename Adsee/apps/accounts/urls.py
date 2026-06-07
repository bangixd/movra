from django.urls import path
from accounts.views import UserDetailAPIView, RequestOTPView, VerifyOTPView

urlpatterns = [
    path("auth/otp/", RequestOTPView.as_view(), name="request_otp"),
    path("auth/otp/verify/", VerifyOTPView.as_view(), name="verify_otp"),
    path('user/', UserDetailAPIView.as_view(), name='user_detail'),
]