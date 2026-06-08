from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from campaigns.services.invoice_service import InvoiceService
from utils.permissions import IsOwnerOrAdmin


class CampaignInvoiceViewSet(ModelViewSet):
    """
    مدیریت فاکتورهای کمپین
    """
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return InvoiceService.get_queryset(self.request.user)

    def get_serializer_class(self):
        return InvoiceService.get_serializer_class(self.action)

    @action(detail=True, methods=['patch'])
    def pay(self, request, pk=None):
        """علامت‌گذاری فاکتور به‌عنوان پرداخت‌شده (فقط ادمین یا درگاه پرداخت)"""
        invoice = self.get_object()
        try:
            updated_invoice = InvoiceService.mark_as_paid(invoice)
            serializer = self.get_serializer(updated_invoice)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)