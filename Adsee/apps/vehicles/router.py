from rest_framework.routers import DefaultRouter
from .views import VehicleTypeViewSet, VehicleViewSet

router = DefaultRouter()
router.register(r'types', VehicleTypeViewSet, basename='vehicle-type')
router.register(r'', VehicleViewSet, basename='vehicle')