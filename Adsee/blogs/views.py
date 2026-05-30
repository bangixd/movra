from rest_framework import viewsets, permissions
from .models import Post
from .serializers import PostListSerializer, PostDetailSerializer

class PublicPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.filter(is_published=True)
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer