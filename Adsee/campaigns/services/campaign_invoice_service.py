import uuid
from datetime import timedelta
from django.utils import timezone
from ..models import CampaignInvoice


class CampaignInvoiceService:

    @staticmethod
    def generate_invoice(cost):

        invoice = CampaignInvoice.objects.create(
            campaign=cost.campaign,
            campaign_cost=cost,
            invoice_number=str(uuid.uuid4())[:12],
            status="ISSUED",
            subtotal_price=cost.subtotal_price,
            discount_amount=cost.discount_amount,
            tax_amount=cost.tax_amount,
            total_price=cost.total_price,
            expires_at=timezone.now() + timedelta(minutes=30),
            snapshot={
                "items": list(
                    cost.items.values(
                        "title",
                        "quantity",
                        "unit_price",
                        "total_price"
                    )
                )
            }
        )

        cost.mark_pending_payment()

        return invoice
