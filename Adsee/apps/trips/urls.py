from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import TripViewSet, DriverHomeView, rate_driver

router = DefaultRouter()
router.register(r'', TripViewSet, basename='trip')

urlpatterns = [
    path('home/', DriverHomeView.as_view(), name='driver-home'),
    path('<int:trip_id>/rate/', rate_driver, name='rate-driver'),

] + router.urls