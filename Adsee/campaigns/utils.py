from .models import CampaignInvoice
from django.utils import timezone


def generate_invoice_number(campaign):
    today = timezone.now().strftime("%Y%m%d")
    count = CampaignInvoice.objects.filter(
        created_at__date=timezone.now().date()
    ).count() + 1
    return f"INV-{today}-{count:04d}"
