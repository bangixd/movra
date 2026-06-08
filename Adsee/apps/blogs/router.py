from rest_framework.routers import DefaultRouter
from blogs.views import PublicPostViewSet
from blogs.admin import AdminPostViewSet

router = DefaultRouter()
router.register(r'admin', AdminPostViewSet, basename='admin-post')
router.register(r'', PublicPostViewSet, basename='public-post')