from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from .models import Brand, BrandCategory
from rest_framework.decorators import action
from .serializers import BrandListSerializer, BrandCreateUpdateSerializer, BrandCategorySerializer
from permissions import IsClientUser


class BrandViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsClientUser]

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return BrandListSerializer
        return BrandCreateUpdateSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Brand.objects.filter(client__user=user)

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        return qs

    def perform_create(self, serializer):
        serializer.save(client=self.request.user.client_profile, status='PENDING')

    @action(detail=True, methods=['patch'])
    def review(self, request, pk=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        brand = self.get_object()
        new_status = request.data.get('status')
        if new_status not in ['APPROVED', 'REJECTED']:
            return Response({"error": "وضعیت نامعتبر"}, status=400)
        brand.status = new_status
        brand.save()
        return Response(BrandListSerializer(brand).data)

class BrandCategoryListView(viewsets.ReadOnlyModelViewSet):
    queryset = BrandCategory.objects.filter(is_active=True)
    serializer_class = BrandCategorySerializer
    permission_classes = [IsAuthenticated]
