from rest_framework import viewsets, permissions
from rest_framework.generics import ListAPIView
from blogs.models import Post, Category
from blogs.serializers import PostListSerializer, PostDetailSerializer, CategorySerializer


class PublicPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    نمایش عمومی پست‌های منتشرشدهٔ وبلاگ.

    ### متدهای اصلی:
    - **GET /blog/posts/** – لیست پست‌های منتشرشده (خلاصه)
      - پارامتر اختیاری: `?category=slug` برای فیلتر بر اساس دسته‌بندی
    - **GET /blog/posts/{id}/** – جزئیات کامل یک پست (شامل بلوک‌ها)

    ### دسترسی:
    - عمومی (بدون نیاز به احراز هویت)

    ### نمونه پاسخ (لیست):
    ```json
    [
        {
            "id": 1,
            "title": "عنوان پست",
            "slug": "post-slug",
            "image": "/media/blog/image.jpg",
            "estimated_reading_time": 5,
            "published_at": "2026-06-10T10:00:00Z",
            "category": {"id": 1, "name": "دسته‌بندی"}
        }
    ]
    """
    permission_classes = [permissions.AllowAny]
    queryset = Post.objects.filter(is_published=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer

    def get_queryset(self):
        category_slug = self.request.query_params.get('category')
        queryset = Post.objects.filter(is_published=True)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset.order_by('-published_at', '-created_at')


class CategoryListView(ListAPIView):
    """
    لیست دسته‌بندی‌های وبلاگ.

    ### GET /blog/categories/
    برگرداندن همهٔ دسته‌بندی‌های موجود (بدون محدودیت).

    ### دسترسی:
    - عمومی (بدون نیاز به احراز هویت)

    ### نمونه پاسخ:
    ```json
    [
        {
            "id": 1,
            "name": "تکنولوژی",
            "slug": "technology"
        },
        {
            "id": 2,
            "name": "کسب‌و‌کار",
            "slug": "business"
        }
    ]
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()