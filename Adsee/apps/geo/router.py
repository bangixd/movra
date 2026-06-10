from rest_framework.routers import DefaultRouter
from geo.views import (
    ProvinceViewSet, CityViewSet, NeighborhoodViewSet,
    SuggestedRouteViewSet, DriverLocationViewSet
)

router = DefaultRouter()
router.register(r'provinces', ProvinceViewSet)
router.register(r'cities', CityViewSet)
router.register(r'neighborhoods', NeighborhoodViewSet)
router.register(r'routes', SuggestedRouteViewSet)
router.register(r'driver-locations', DriverLocationViewSet)