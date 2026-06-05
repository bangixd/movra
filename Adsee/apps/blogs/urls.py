from rest_framework.routers import DefaultRouter
from .views import PublicPostViewSet
from .admin_views import AdminPostViewSet

router = DefaultRouter()
router.register(r'admin', AdminPostViewSet, basename='admin-post')
router.register(r'', PublicPostViewSet, basename='public-post')

urlpatterns = router.urls