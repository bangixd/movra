from rest_framework import viewsets, permissions
from blogs.models import Post, Category, Author, PostBlock
from blogs.serializers import PostDetailSerializer, PostListSerializer, CategorySerializer, AuthorSerializer, PostBlockSerializer
from utils.permissions import IsAdminUser


class AdminPostViewSet(viewsets.ModelViewSet):
    """
     مدیریت کامل پست‌های وبلاگ توسط ادمین.

     ## 🛠️ متدها

     ### لیست پست‌ها
     `GET /v1/blogs/admin/posts/`

     برگرداندن لیست همهٔ پست‌ها (شامل پیش‌نویس‌ها و منتشرشده‌ها).

     ### دریافت یک پست
     `GET /v1/blogs/admin/posts/{id}/`

     برگرداندن جزئیات کامل یک پست به‌همراه بلوک‌های محتوا.

     ### ایجاد پست جدید
     `POST /v1/blogs/admin/posts/`

     ایجاد یک پست جدید با قابلیت ارسال هم‌زمان بلوک‌های محتوا.

     #### 📥 نمونه درخواست
     ```json
     {
         "title": "عنوان پست جدید",
         "slug": "new-post-title",
         "author": 1,
         "category": 2,
         "image": null,
         "estimated_reading_time": 5,
         "is_published": true,
         "published_at": "2026-06-15T10:30:00Z",
         "blocks": [
             {
                 "block_type": "heading",
                 "title": "فصل اول: شروع کار",
                 "order": 1
             },
             {
                 "block_type": "text",
                 "text": "این متن اصلی مقاله است که در این بخش قرار می‌گیرد...",
                 "order": 2
             },
             {
                 "block_type": "image",
                 "image": "/media/blog/blocks/sample.jpg",
                 "order": 3
             },
             {
                 "block_type": "quote",
                 "text": "جمله‌ای الهام‌بخش از یک شخص معروف",
                 "order": 4
             }
         ]
     }

     نمونه درخواست ساده (بدون بلوک)
    json
    {
        "title": "عنوان پست جدید",
        "slug": "new-post-title",
        "author": 1,
        "category": 2,
        "is_published": false
    }
    نمونه پاسخ موفق
        {
        "id": 15,
        "title": "عنوان پست جدید",
        "slug": "new-post-title",
        "author": {
            "id": 1,
            "full_name": "ابوالفضل سیاح",
            "bio": "توسعه‌دهندهٔ فول‌استک",
            "avatar": "/media/blog/authors/avatar.jpg",
            "email": "abolfazls4yy4h@gmail.com",
            "website": "https://example.com"
        },
        "category": {
            "id": 2,
            "name": "تکنولوژی",
            "slug": "technology"
        },
        "image": null,
        "estimated_reading_time": 5,
        "published_at": "2026-06-15T10:30:00Z",
        "is_published": true,
        "created_at": "2026-06-15T10:00:00Z",
        "updated_at": "2026-06-15T10:00:00Z",
        "blocks": [
            {
                "id": 1,
                "block_type": "heading",
                "title": "فصل اول: شروع کار",
                "text": "",
                "image": null,
                "order": 1
            },
            {
                "id": 2,
                "block_type": "text",
                "title": "",
                "text": "این متن اصلی مقاله است که در این بخش قرار می‌گیرد...",
                "image": null,
                "order": 2
            }
        ]
    }
    """
    queryset = Post.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer


class AdminCategoryViewSet(viewsets.ModelViewSet):
    """
    مدیریت دسته‌بندی‌ها توسط ادمین.

    GET /blogs/admin/categories/ – لیست
    POST /blogs/admin/categories/ – ایجاد
    GET /blogs/admin/categories/{id}/ – جزئیات
    PUT/PATCH /blogs/admin/categories/{id}/ – ویرایش
    DELETE /blogs/admin/categories/{id}/ – حذف
    """
    permission_classes = [IsAdminUser]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class AdminAuthorViewSet(viewsets.ModelViewSet):
    """
    مدیریت نویسندگان وبلاگ توسط ادمین.

    ### متدها:
    - **GET /api/blog/admin/authors/**: لیست همهٔ نویسندگان
    - **POST /api/blog/admin/authors/**: ایجاد نویسندهٔ جدید
    - **GET /api/blog/admin/authors/{id}/**: جزئیات یک نویسنده
    - **PUT/PATCH /api/blog/admin/authors/{id}/**: ویرایش نویسنده
    - **DELETE /api/blog/admin/authors/{id}/**: حذف نویسنده

    ### محدودیت‌ها:
    - فقط ادمین دسترسی دارد.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminUser]


class AdminPostBlockViewSet(viewsets.ModelViewSet):
    """
    مدیریت بلوک‌های محتوای پست توسط ادمین.

    ### متدها:
    - **GET /api/blog/admin/post-blocks/**: لیست همهٔ بلوک‌ها (با فیلتر ?post=1)
    - **POST /api/blog/admin/post-blocks/**: ایجاد بلوک جدید برای یک پست
    - **GET /api/blog/admin/post-blocks/{id}/**: جزئیات یک بلوک
    - **PUT/PATCH /api/blog/admin/post-blocks/{id}/**: ویرایش بلوک
    - **DELETE /api/blog/admin/post-blocks/{id}/**: حذف بلوک

    ### پارامترهای فیلتر:
    - `?post=1`: فقط بلوک‌های مربوط به پست شماره ۱ را برگردان

    ### محدودیت‌ها:
    - فقط ادمین دسترسی دارد.
    """
    serializer_class = PostBlockSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = PostBlock.objects.all()
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset