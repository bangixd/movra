from rest_framework import serializers
from blogs.models import Post, PostBlock, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class PostBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostBlock
        fields = ['id', 'block_type', 'title', 'text', 'image', 'order']


class PostListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'image',
            'estimated_reading_time', 'published_at',
            'category_name', 'author_name'
        ]


class PostDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author = serializers.CharField(source='author.get_full_name', read_only=True)
    blocks = PostBlockSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'author', 'category',
            'image', 'estimated_reading_time', 'published_at',
            'is_published', 'created_at', 'updated_at', 'blocks'
        ]