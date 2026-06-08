from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drivers.serializers import DriverDocumentSerializer
from drivers.services.driver_document_service import DriverDocumentService
from utils.permissions import IsDriverOrAdmin


class DriverDocumentViewSet(viewsets.ModelViewSet):
    """
    مدیریت مدارک راننده.

    ### متدهای اصلی:
    - **GET /drivers/documents/**: لیست مدارک (ادمین: همه، راننده: فقط مدارک خودش)
    - **POST /drivers/documents/**: آپلود مدرک جدید
      - Body (multipart): `document_type`, `file`
      - پس از اولین آپلود، مرحلهٔ ثبت‌نام به VERIFICATION تغییر می‌کند
    - **GET /drivers/documents/{id}/**: جزئیات یک مدرک
    - **DELETE /drivers/documents/{id}/**: حذف مدرک

    ### اکشن‌های اختصاصی:
    - **PATCH /drivers/documents/{id}/review/**: بررسی مدرک (فقط ادمین)
      - Body: `{"status": "APPROVED"}` یا `{"status": "REJECTED", "reject_reason": "..."}`
      - Response: اطلاعات مدرک به‌روزرسانی‌شده

    ### نکات:
    - پس از تأیید همهٔ مدارک، kyc_status به APPROVED تغییر می‌کند.
    - پس از تأیید، مرحلهٔ ثبت‌نام به CONTRACT می‌رود.
    """
    serializer_class = DriverDocumentSerializer
    permission_classes = [IsAuthenticated, IsDriverOrAdmin]

    def get_queryset(self):
        return DriverDocumentService.get_queryset(self.request.user)

    def create(self, request, *args, **kwargs):
        """آپلود مدرک جدید"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ✅ Pass the serializer, not serializer.validated_data directly
        document = DriverDocumentService.create_document(
            user=request.user,
            serializer=serializer  # ← pass the serializer, not validated_data
        )

        output_serializer = self.get_serializer(document)
        headers = self.get_success_headers(output_serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
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
            updated_document = DriverDocumentService.review_document(
                document, new_status, reject_reason
            )
            serializer = self.get_serializer(updated_document)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
