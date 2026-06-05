from rest_framework import serializers
from .models import Post

class PostListSerializer(serializers.ModelSerializer):
    """خلاصه برای لیست (بدون محتوای کامل)"""
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'image', 'created_at']

class PostDetailSerializer(serializers.ModelSerializer):
    """جزئیات کامل یک پست"""
    class Meta:
        model = Post
        fields = '__all__'