from rest_framework import viewsets, permissions
from .models import SupportContent
from .serializers import SupportContentSerializer

class SupportContentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SupportContent.objects.filter(is_active=True)
    serializer_class = SupportContentSerializer
    permission_classes = [permissions.IsAuthenticated]