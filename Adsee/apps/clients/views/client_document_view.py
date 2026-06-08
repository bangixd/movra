from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from clients.models import ClientDocument
from clients.serializers import ClientDocumentSerializer
from clients.services.client_document_service import ClientDocumentService
from utils.permissions import IsClientOrAdmin


class ClientDocumentViewSet(viewsets.ModelViewSet):
    """
    مدیریت مدارک احراز هویت کلاینت.

    ### متدهای اصلی:
    - **GET /clients/documents/**: لیست مدارک کاربر (ادمین: همه)
    - **POST /clients/documents/**: آپلود مدرک جدید
      - Body (multipart): `document_type`, `file`
    - **GET /clients/documents/{id}/**: جزئیات یک مدرک
    - **DELETE /clients/documents/{id}/**: حذف مدرک

    ### اکشن‌های اختصاصی:
    - **PATCH /clients/documents/{id}/review/**: بررسی مدرک (فقط ادمین)
      - Body: `{"status": "APPROVED"}` یا `{"status": "REJECTED", "reject_reason": "..."}`
      - Response: اطلاعات مدرک به‌روزرسانی‌شده

    ### نکات:
    - پس از آپلود اولین مدرک، مرحلهٔ KYC به VERIFICATION تغییر می‌کند.
    - پس از تأیید یا رد مدرک، وضعیت کلی KYC پروفایل به‌روز می‌شود.
    """
    serializer_class = ClientDocumentSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get_queryset(self):
        return ClientDocumentService.get_queryset(self.request.user)

    def perform_create(self, serializer):
        # استفاده از سرویس برای ایجاد و به‌روزرسانی KYC
        ClientDocumentService.create_document(
            user=self.request.user,
            validated_data=serializer.validated_data
        )

    @action(detail=True, methods=['patch'])
    def review(self, request, pk=None):
        """بررسی مدرک توسط ادمین"""
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        document = self.get_object()
        new_status = request.data.get('status')
        reject_reason = request.data.get('reject_reason', '')

        try:
            updated_document = ClientDocumentService.review_document(
                document, new_status, reject_reason
            )
            serializer = self.get_serializer(updated_document)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)