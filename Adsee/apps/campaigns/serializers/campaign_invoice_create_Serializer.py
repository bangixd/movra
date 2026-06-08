from rest_framework import serializers
from datetime import timedelta
from campaigns.models import Campaign, CampaignInvoice
from utils.generate_invoice_number import generate_invoice_number
from django.utils import timezone

class CampaignInvoiceCreateSerializer(serializers.ModelSerializer):
    campaign = serializers.PrimaryKeyRelatedField(
        queryset=Campaign.objects.all()  # یا محدودشده به کمپین‌های آماده فاکتور
    )

    class Meta:
        model = CampaignInvoice
        fields = ['campaign']  # فقط campaign از سمت فرستنده
        # سایر فیلدها در create مقداردهی می‌شن

    def validate_campaign(self, campaign):
        # مثلاً چک کن که کمپین قبلاً فاکتور نداره (چون OneToOne)
        if CampaignInvoice.objects.filter(campaign=campaign).exists():
            raise serializers.ValidationError("این کمپین از قبل فاکتور دارد.")
        # چک کن که وضعیت کمپین قابل صدور فاکتور باشه
        return campaign

    def create(self, validated_data):
        campaign = validated_data['campaign']

        # گرفتن آخرین CampaignCost مرتبط با کمپین
        campaign_cost = campaign.costs.last()  # یا campaign.campaign_cost اگر OneToOne هست
        if not campaign_cost:
            raise serializers.ValidationError("هزینه‌ای برای این کمپین محاسبه نشده است.")

        # محاسبه مبالغ بر اساس CampaignCost
        # فرض: CampaignCost شامل subtotal, discount, tax, total به‌عنوان فیلد/متد
        subtotal = campaign_cost.subtotal_price
        discount = campaign_cost.discount_amount
        tax = campaign_cost.tax_amount
        total = campaign_cost.total_price

        # ساختن snapshot از آیتم‌ها و قوانین
        snapshot_data = {
            "cost_items": list(campaign_cost.items.values()),  # فرضاً items رابطه‌ست
            "pricing_rules": "..."  # می‌تونی خلاصه‌ای از قوانین ذخیره کنی
        }

        # تولید شماره فاکتور
        invoice_number = generate_invoice_number(campaign)

        invoice = CampaignInvoice.objects.create(
            campaign=campaign,
            campaign_cost=campaign_cost,
            invoice_number=invoice_number,
            status=CampaignInvoice.Status.ISSUED,
            subtotal_price=subtotal,
            discount_amount=discount,
            tax_amount=tax,
            total_price=total,
            expires_at=timezone.now() + timedelta(days=15),
            snapshot=snapshot_data,
        )
        return invoice
