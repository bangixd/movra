from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BrandViewSet, BrandCategoryListView
from .admin_views import AdminBrandCategoryViewSet

router = DefaultRouter()
router.register(r'', BrandViewSet, basename='brand')
router.register(r'admin/categories', AdminBrandCategoryViewSet, basename='admin-brand-category')
urlpatterns = [
    path('', include(router.urls)),
    path('categories/', BrandCategoryListView.as_view({'get': 'list'}), name='brand-categories'),
]
