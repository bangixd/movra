from django.db import models
from django.utils import timezone

class CampaignInvoice(models.Model):

    class Status(models.TextChoices):
        ISSUED = "ISSUED", "Issued"
        PAID = "PAID", "Paid"
        EXPIRED = "EXPIRED", "Expired"
        VOID = "VOID", "Void"

    campaign = models.ForeignKey(
        "Campaign",
        on_delete=models.CASCADE,
        related_name="invoices"  # جمع بسته شود
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices)

    subtotal_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2)
    total_price = models.DecimalField(max_digits=14, decimal_places=2)

    expires_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)

    snapshot = models.JSONField(default=dict)

    MODIFICATION_TYPES = [
        ('EXTEND', 'تمدید کمپین'),
        ('ADD_VEHICLES', 'افزایش خودرو'),
        ('CHANGE_DESIGN', 'تغییر بنر'),
    ]
    modification_type = models.CharField(max_length=20, choices=MODIFICATION_TYPES, null=True, blank=True)
    modification_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_expired(self):
        return self.status == self.Status.EXPIRED or (
                self.status == self.Status.ISSUED and self.expires_at and timezone.now() > self.expires_at
        )

