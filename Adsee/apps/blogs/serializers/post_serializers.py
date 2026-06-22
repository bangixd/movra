from rest_framework import serializers
from blogs.models import Post, PostBlock, Category, Author
from accounts.models import User


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class PostBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostBlock
        fields = ['id', 'post', 'block_type', 'title', 'text', 'image', 'order']


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'full_name', 'bio', 'avatar', 'email', 'website']


class PostListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author = AuthorSerializer(read_only=True)
    blocks = PostBlockSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'image',
            'estimated_reading_time','is_published' 'published_at',
            'category', 'author', 'blocks'
        ]




class PostDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author = AuthorSerializer(read_only=True)
    blocks = PostBlockSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'author', 'category',
            'image', 'estimated_reading_time', 'published_at',
            'is_published', 'created_at', 'updated_at', 'blocks'
        ]