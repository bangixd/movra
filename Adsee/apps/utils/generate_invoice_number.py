from django.utils import timezone
from campaigns.models import CampaignInvoice

def generate_invoice_number():
    """
    تولید شماره فاکتور یکتا به فرمت:
    INV-YYYYMMDD-XXXX
    که XXXX یک عدد ۴ رقمی ترتیبی در آن روز است.
    """
    today = timezone.now().strftime('%Y%m%d')
    # شمارش فاکتورهایی که امروز ساخته شده‌اند
    count_today = CampaignInvoice.objects.filter(
        created_at__date=timezone.now().date()
    ).count() + 1
    return f"INV-{today}-{count_today:04d}"