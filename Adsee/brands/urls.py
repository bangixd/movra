from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import BrandViewSet, BrandCategoryListView, AdminBrandCategoryViewSet

router = DefaultRouter()
router.register(r'', BrandViewSet, basename='brand')
router.register(r'admin/categories', AdminBrandCategoryViewSet, basename='admin-brand-category')
urlpatterns = router.urls + [
    path('categories/', BrandCategoryListView.as_view({'get': 'list'}), name='brand-categories'),
]
