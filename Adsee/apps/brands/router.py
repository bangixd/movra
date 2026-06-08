from rest_framework.routers import DefaultRouter
from brands.views import BrandViewSet, BrandCategoryListView
from brands.admin.admin_views import AdminBrandCategoryViewSet

router = DefaultRouter()
router.register(r'', BrandViewSet, basename='brand')
router.register(r'admin/categories', AdminBrandCategoryViewSet, basename='admin-brand-category')