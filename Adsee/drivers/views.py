from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import DriverProfile, DriverDocument
from .serializers import DriverProfileSerializer, DriverDocumentSerializer

class IsDriverOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_staff or getattr(request.user, 'role', None) == 'DRIVER'

class DriverProfileViewSet(viewsets.ModelViewSet):
    serializer_class = DriverProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsDriverOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return DriverProfile.objects.all()
        return DriverProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['patch'])
    def accept_contract(self, request):
        """مرحله ۴: پذیرش قرارداد"""
        profile = self.get_queryset().first()
        if not profile:
            return Response({"error": "پروفایلی یافت نشد"}, status=404)
        if profile.kyc_status != 'APPROVED':
            return Response({"error": "ابتدا باید احراز هویت شما تأیید شود"}, status=400)
        profile.is_contract_accepted = True
        profile.registration_step = DriverProfile.RegistrationStep.CONTRACT
        profile.save()
        return Response(DriverProfileSerializer(profile).data)


class DriverDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DriverDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsDriverOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return DriverDocument.objects.all()
        return DriverDocument.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        # بعد از آپلود اولین مدرک، مرحله را به ۳ ببر
        profile = self.request.user.driver_profile
        if profile.registration_step == DriverProfile.RegistrationStep.DOCUMENTS:
            profile.registration_step = DriverProfile.RegistrationStep.VERIFICATION
            profile.kyc_submitted_at = timezone.now()
            profile.save(update_fields=['registration_step', 'kyc_submitted_at'])

    @action(detail=True, methods=['patch'])
    def review(self, request, pk=None):
        """بررسی مدرک توسط ادمین"""
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        doc = self.get_object()
        new_status = request.data.get('status')
        if new_status not in [DriverDocument.ApprovalStatus.APPROVED, DriverDocument.ApprovalStatus.REJECTED]:
            return Response({"error": "وضعیت نامعتبر"}, status=400)

        doc.status = new_status
        doc.reviewed_at = timezone.now()
        if new_status == DriverDocument.ApprovalStatus.REJECTED:
            doc.reject_reason = request.data.get('reject_reason', '')
        doc.save()

        # به‌روزرسانی وضعیت KYC پروفایل
        self._update_kyc_status(doc.user)

        return Response(DriverDocumentSerializer(doc).data)

    def _update_kyc_status(self, user):
        """اگر همه مدارک تأیید شدند، kyc_status = APPROVED"""
        profile = user.driver_profile
        docs = DriverDocument.objects.filter(user=user)
        if docs.filter(status=DriverDocument.ApprovalStatus.REJECTED).exists():
            profile.kyc_status = 'REJECTED'
        elif docs.exists() and all(d.status == DriverDocument.ApprovalStatus.APPROVED for d in docs):
            profile.kyc_status = 'APPROVED'
            if profile.registration_step == DriverProfile.RegistrationStep.VERIFICATION:
                profile.registration_step = DriverProfile.RegistrationStep.CONTRACT
        else:
            profile.kyc_status = 'PENDING'
        profile.kyc_reviewed_at = timezone.now()
        profile.save()