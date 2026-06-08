import json
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from campaigns.models import CampaignInvoice
from utils.generate_invoice_number import generate_invoice_number


class InvoiceService:
    """سرویس مدیریت فاکتورها"""

    @staticmethod
    def create_modification_invoice(
            campaign,
            modification_type: str,
            extra_amount: Decimal,
            modification_data: dict,
            snapshot_extra: dict = None
    ) -> CampaignInvoice:
        """
        ایجاد فاکتور برای تغییرات کمپین (افزایش خودرو، تمدید، تغییر طراحی)

        Args:
            campaign: نمونهٔ کمپین
            modification_type: نوع تغییر (ADD_VEHICLES, EXTEND, CHANGE_DESIGN)
            extra_amount: مبلغ خالص (قبل از مالیات)
            modification_data: اطلاعات تغییرات
            snapshot_extra: داده‌های اضافی برای snapshot

        Returns:
            نمونهٔ فاکتور ساخته‌شده
        """
        subtotal = extra_amount
        discount = Decimal('0')
        tax = extra_amount * Decimal('0.09')
        total = extra_amount * Decimal('1.09')

        # ساخت snapshot
        snapshot = {
            'extra_cost': float(extra_amount),
            'total': float(total),
        }
        if snapshot_extra:
            snapshot.update(snapshot_extra)

        invoice = CampaignInvoice.objects.create(
            campaign=campaign,
            invoice_number=generate_invoice_number(),
            subtotal_price=subtotal,
            discount_amount=discount,
            tax_amount=tax,
            total_price=total,
            expires_at=timezone.now() + timedelta(minutes=15),
            status=CampaignInvoice.Status.ISSUED,
            modification_type=modification_type,
            modification_data=modification_data,
            snapshot=snapshot,
        )
        return invoice

    @staticmethod
    def get_queryset(user):
        """
        Return invoices based on user role.
        - Admin: all invoices
        - Client: only invoices for their own brands
        """
        if not user.is_authenticated:
            return CampaignInvoice.objects.none()
        if user.is_staff:
            return CampaignInvoice.objects.all()
        return CampaignInvoice.objects.filter(campaign__client__user=user)

    @staticmethod
    def get_serializer_class(action: str):
        """Return the appropriate serializer class based on action."""
        from campaigns.serializers import (
            CampaignInvoiceCreateSerializer,
            CampaignInvoiceReadSerializer,
        )
        if action == 'create':
            return CampaignInvoiceCreateSerializer
        return CampaignInvoiceReadSerializer

    @staticmethod
    def mark_as_paid(invoice) -> CampaignInvoice:
        """
        Mark an invoice as PAID.
        Raises: ValueError if the invoice is not in ISSUED status.
        """
        if invoice.status != CampaignInvoice.Status.ISSUED:
            raise ValueError("فاکتور قابل پرداخت نیست.")
        invoice.status = CampaignInvoice.Status.PAID
        invoice.paid_at = timezone.now()
        invoice.save()
        return invoice