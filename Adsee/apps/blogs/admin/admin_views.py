from rest_framework import viewsets, permissions
from blogs.models import Post, Category
from blogs.serializers import PostDetailSerializer, CategorySerializer
from utils.permissions import IsAdminUser

class AdminPostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostDetailSerializer
    permission_classes = [IsAdminUser]


class AdminCategoryViewSet(viewsets.ModelViewSet):
    """
    مدیریت دسته‌بندی‌ها توسط ادمین.

    GET /blog/admin/categories/ – لیست
    POST /blog/admin/categories/ – ایجاد
    GET /blog/admin/categories/{id}/ – جزئیات
    PUT/PATCH /blog/admin/categories/{id}/ – ویرایش
    DELETE /blog/admin/categories/{id}/ – حذف
    """
    permission_classes = [IsAdminUser]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()