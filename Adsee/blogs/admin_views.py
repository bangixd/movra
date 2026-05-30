from rest_framework import viewsets, permissions
from .models import Post
from .serializers import PostDetailSerializer
from permissions import IsAdminUser

class AdminPostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostDetailSerializer
    permission_classes = [IsAdminUser]