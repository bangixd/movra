import random
import string
from django.utils import timezone

def generate_invoice_number():
    now = timezone.now()
    date_part = now.strftime('%Y%m%d')
    # Add seconds and random suffix to avoid duplicates
    time_part = now.strftime('%H%M%S')
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"INV-{date_part}-{time_part}-{random_suffix}"
