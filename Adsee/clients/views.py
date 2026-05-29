from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
# from django.core import cache
from rest_framework.throttling import UserRateThrottle
from rest_framework import viewsets, serializers, status
from rest_framework.permissions import IsAuthenticated
from .serializers import ClientProfileSerializer, ClientDocumentSerializer
from .models import ClientProfile, ClientDocument
from permissions import IsClientUser, IsClientOrAdmin, IsOwnerOrAdmin
from rest_framework.response import Response
from rest_framework.decorators import action


class ClientProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin, IsOwnerOrAdmin]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'POST':
            try:
                kwargs['data']['user'] = self.request.user.pk
            except:
                pass
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save()
        # self.process_kyc(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        # self.process_kyc(instance)

    def perform_create(self, serializer):
        # اگر در درخواست، user مشخص شده باشد، از آن استفاده کن
        user_id = self.request.data.get('user')
        if user_id:
            try:
                user = get_object_or_404(get_user_model(), pk=user_id)
                serializer.save(user=user)
            except ValueError:  # اگر user_id عدد نباشد
                raise serializers.ValidationError({"user": "شناسه کاربر نامعتبر است."})
        else:
            # اگر user مشخص نشده باشد، باید خطا بدهد (چون برای ادمین هم الزامی است)
            raise serializers.ValidationError({"user": "شناسه کاربر الزامی است."})


class ClientDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = ClientDocumentSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return ClientDocument.objects.all()
        return ClientDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def review(self, request, pk=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        doc = self.get_object()
        new_status = request.data.get('status')
        if new_status not in [ClientDocument.ApprovalStatus.APPROVED, ClientDocument.ApprovalStatus.REJECTED]:
            return Response({"error": "invalid status"}, status=400)

        doc.status = new_status
        doc.reviewed_at = timezone.now()
        if new_status == ClientDocument.ApprovalStatus.REJECTED:
            doc.reject_reason = request.data.get('reject_reason', '')
        doc.save()
        return Response(ClientDocumentSerializer(doc).data)