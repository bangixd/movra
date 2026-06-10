from rest_framework.routers import DefaultRouter
from .views import PrintShopProfileViewSet

router = DefaultRouter()
router.register(r'profile', PrintShopProfileViewSet, basename='print_shops')