from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import BrandViewSet, BrandCategoryListView

router = DefaultRouter()
router.register(r'', BrandViewSet, basename='brand')
urlpatterns = router.urls + [
    path('categories/', BrandCategoryListView.as_view({'get': 'list'}), name='brand-categories'),
]
