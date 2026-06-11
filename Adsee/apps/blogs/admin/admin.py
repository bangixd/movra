from django.contrib import admin
from blogs.models import Post, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_published', 'published_at', 'estimated_reading_time', 'created_at']
    list_filter = ['is_published', 'category', 'author']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}