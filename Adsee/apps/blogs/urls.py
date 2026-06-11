from blogs.router import router
from django.urls import path, include
from blogs.views import CategoryListView


urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='blog-categories'),
    path('', include(router.urls)),
]