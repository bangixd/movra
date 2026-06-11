from django.urls import path
from .views import DriverHomeView, rate_driver

from .router import router

urlpatterns = [
    path('home/', DriverHomeView.as_view(), name='driver-home'),
    path('<int:trip_id>/rate/', rate_driver, name='rate-driver'),

] + router.urls