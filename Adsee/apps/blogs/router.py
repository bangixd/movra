from rest_framework.routers import DefaultRouter
from blogs.views import PublicPostViewSet
from blogs.admin import AdminPostViewSet, AdminCategoryViewSet, AdminAuthorViewSet, AdminPostBlockViewSet

router = DefaultRouter()
router.register(r'posts', PublicPostViewSet, basename='public-post')
router.register(r'admin', AdminPostViewSet, basename='admin-post')
router.register(r'admin-categories', AdminCategoryViewSet, basename='admin-category')
router.register(r'admin-authors', AdminAuthorViewSet, basename='admin-author')
router.register(r'admin-post-blocks', AdminPostBlockViewSet, basename='admin-post-block')
