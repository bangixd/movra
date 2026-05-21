from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404
# from django.core import cache
from rest_framework.throttling import UserRateThrottle
from rest_framework import viewsets, serializers
from rest_framework.permissions import IsAuthenticated
from utils import send_kyc_to_external_service
from .serializers import ClientProfileSerializer
from .models import ClientProfile
from permissions import IsClientUser, IsOwnerOrAdmin


class ClientProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated, IsClientUser]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    def process_kyc(self, instance):
        document = instance.id_or_registration_copy
        if not document:
            return
        # existing_document = DriverDocument.objects.filter(
        #     user=instance.user,
        #     document_type=document
        # ).first()
        # if existing_document and existing_document.status != instance.KYCStatus.REJECTED:
        #     # اگر مدرک از قبل وجود دارد و رد نشده، اجازه آپلود مجدد نمی‌دهیم مگر اینکه بخواهیم overwrite کنیم
        #     # یا می‌توانیم اینجا منطق overwrite را اضافه کنیم
        #     return Response(
        #         {
        #             "detail":
        #             f"A document of type '{document}' already exists and is not rejected.
        #             Please update it if necessary."},
        #         status=status.HTTP_409_CONFLICT
        #     )
        try:
            response = send_kyc_to_external_service(instance, document)
        except:
            return
        return response

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

    def get_object(self):
        user = self.request.user
        if user.is_anonymous:
            return None

        try:
            client_profile = ClientProfile.objects.get(user=user)
            return client_profile
        except ClientProfile.DoesNotExist:
            raise Http404("Client profile not found for this user.")

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
