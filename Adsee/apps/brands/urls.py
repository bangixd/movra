from django.urls import path, include
from brands.views import BrandCategoryListView
from .router import router

urlpatterns = [
    path('', include(router.urls)),
    path('categories/', BrandCategoryListView.as_view({'get': 'list'}), name='brand-categories'),
]
