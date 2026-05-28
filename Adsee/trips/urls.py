from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import TripViewSet, DriverHomeView

router = DefaultRouter()
router.register(r'', TripViewSet, basename='trip')

urlpatterns = [
    path('home/', DriverHomeView.as_view(), name='driver-home'),
] + router.urls