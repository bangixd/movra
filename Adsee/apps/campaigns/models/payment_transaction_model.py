from django.db import models
from .campaign_invoice_model import CampaignInvoice

class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        PENDING = 'PENDING', 'Pending'
        SUCCESSFUL = 'SUCCESSFUL', 'Successful'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    invoice = models.ForeignKey(CampaignInvoice, on_delete=models.PROTECT, related_name='transactions')
    authority = models.CharField(max_length=200, unique=True)  # شناسه یکتای زرین‌پال
    ref_id = models.CharField(max_length=200, blank=True, null=True)  # شماره پیگیری
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    response_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction {self.authority} - {self.status}"

