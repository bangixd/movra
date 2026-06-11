from rest_framework.routers import DefaultRouter
from blogs.views import PublicPostViewSet
from blogs.admin import AdminPostViewSet, AdminCategoryViewSet

router = DefaultRouter()
router.register(r'', PublicPostViewSet, basename='public-post')
router.register(r'admin', AdminPostViewSet, basename='admin-post')
router.register(r'admin-categories', AdminCategoryViewSet, basename='admin-category')
