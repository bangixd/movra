from .models import DriverProfile, DriverDocument
from .serializers import DriverProfileSerializer, DriverDocumentSerializer
from rest_framework.decorators import action
from permissions import IsDriverUser, IsOwnerOrAdmin
from rest_framework import status, viewsets, serializers
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAuthenticated
from django.http import Http404
from rest_framework.response import Response
from django.utils import timezone



class DriverProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = DriverProfile.objects.all()
    serializer_class = DriverProfileSerializer
    permission_classes = [IsDriverUser, IsOwnerOrAdmin]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            raise Http404("user not found.")


class DriverDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DriverDocumentSerializer
    permission_classes = [IsOwnerOrAdmin]

    # def get_queryset(self):
    #     if self.request.user.is_staff:
    #         return DriverDocument.objects.all()
    #     return DriverDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def review(self, request, pk=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        doc = self.get_object()
        new_status = request.data.get('status')
        if new_status not in [DriverDocument.ApprovalStatus.APPROVED, DriverDocument.ApprovalStatus.REJECTED]:
            return Response({"error": "invalid status"}, status=400)

        doc.status = new_status
        doc.reviewed_at = timezone.now()
        if new_status == DriverDocument.ApprovalStatus.REJECTED:
            doc.reject_reason = request.data.get('reject_reason', '')
        doc.save()
        return Response(DriverDocumentSerializer(doc).data)