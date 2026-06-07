from rest_framework import viewsets, permissions
from blogs.models import Post
from blogs.serializers import PostDetailSerializer
from utils.permissions import IsAdminUser

class AdminPostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostDetailSerializer
    permission_classes = [IsAdminUser]