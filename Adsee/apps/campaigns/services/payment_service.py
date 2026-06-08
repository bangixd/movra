import json
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from campaigns.services.pricing import calculate_campaign_cost
from utils.generate_invoice_number import generate_invoice_number
from datetime import datetime
from campaigns.models import CampaignInvoice, PaymentTransaction, Template, BannerType, Campaign
from campaigns.services.campaign_design_service import CampaignDesignService
from services.payment_gateway import ZarinpalGateway


class PaymentService:
    """سرویس مدیریت پرداخت"""

    @staticmethod
    def create_or_get_invoice(campaign) -> CampaignInvoice:
        """
        ایجاد فاکتور جدید برای کمپین یا برگرداندن فاکتور معتبر موجود.
        Args:
            campaign: نمونهٔ کمپین
        Returns:
            نمونهٔ فاکتور آمادهٔ پرداخت
        Raises:
            ValueError: اگر فاکتور منقضی شده باشد
            ConflictError: اگر فاکتور معتبر پرداخت‌نشده وجود داشته باشد
        """
        # بررسی فاکتور ISSUED موجود
        existing = CampaignInvoice.objects.filter(
            campaign=campaign,
            status=CampaignInvoice.Status.ISSUED
        ).first()

        if existing:
            if existing.is_expired:
                existing.status = CampaignInvoice.Status.EXPIRED
                existing.save()
                raise ValueError("فاکتور منقضی شده است. لطفاً دوباره درخواست دهید.")
            else:
                raise ValueError("یک فاکتور فعال برای این کمپین وجود دارد. لطفاً پرداخت را تکمیل کنید.")

        # محاسبهٔ هزینه
        cost = calculate_campaign_cost(campaign)

        # ایجاد فاکتور جدید
        snapshot = json.loads(json.dumps(cost, cls=DjangoJSONEncoder))
        invoice = CampaignInvoice.objects.create(
            campaign=campaign,
            invoice_number=generate_invoice_number(),
            subtotal_price=cost['subtotal'],
            discount_amount=cost.get('discount', Decimal('0')),
            tax_amount=cost['tax'],
            total_price=cost['total'],
            expires_at=timezone.now() + timedelta(minutes=15),
            snapshot=snapshot,
            status=CampaignInvoice.Status.ISSUED,
        )
        return invoice

    @staticmethod
    def initiate_payment(invoice, campaign, phone: str) -> dict:
        """
        شروع فرآیند پرداخت برای یک فاکتور
        Args:
            invoice: نمونهٔ فاکتور
            campaign: نمونهٔ کمپین (برای توضیحات)
            phone: شمارهٔ موبایل پرداخت‌کننده
        Returns:
            dict: {'payment_url': ..., 'invoice_id': ...}
        Raises:
            ConnectionError: در صورت خطا در اتصال به درگاه
        """
        gateway = ZarinpalGateway()
        success, payment_url_or_error, error = gateway.send_request(
            amount=invoice.total_price,
            description=f'کمپین {campaign.slogan}',
            mobile=phone
        )

        if not success:
            invoice.status = CampaignInvoice.Status.VOID
            invoice.save()
            raise ConnectionError(error or "خطا در اتصال به درگاه پرداخت")

        # ثبت تراکنش
        PaymentTransaction.objects.create(
            invoice=invoice,
            authority=payment_url_or_error.split('/')[-1],
            amount=invoice.total_price,
            status=PaymentTransaction.Status.INITIATED
        )

        return {
            'payment_url': payment_url_or_error,
            'invoice_id': invoice.id
        }
    @staticmethod
    def verify_payment(authority: str, status_param: str) -> dict:
        """
        Verify payment and apply all modifications.
        Args:
            authority: Zarinpal authority code
            status_param: 'OK' or 'NOK' from Zarinpal callback
        Returns:
            dict: {'message': ..., 'ref_id': ..., 'status': ...}
        Raises:
            Transaction.DoesNotExist: if authority is invalid
        """
        # ۱. یافتن تراکنش
        transaction = PaymentTransaction.objects.get(authority=authority)
        invoice = transaction.invoice

        # ۲. اگر کاربر پرداخت را لغو کرده بود
        if status_param != 'OK':
            transaction.status = PaymentTransaction.Status.FAILED
            transaction.save()
            return {
                'error': 'پرداخت توسط کاربر لغو شد',
                'status': 'cancelled'
            }

        # ۳. تأیید پرداخت از زرین‌پال
        gateway = ZarinpalGateway()
        success, ref_id = gateway.verify_payment(authority, invoice.total_price)

        if not success:
            transaction.status = PaymentTransaction.Status.FAILED
            transaction.response_data = {'error': ref_id}
            transaction.save()
            return {'error': 'تأیید پرداخت ناموفق', 'status': 'failed'}

        # ۴. بروزرسانی تراکنش و فاکتور
        transaction.status = PaymentTransaction.Status.SUCCESSFUL
        transaction.ref_id = ref_id
        transaction.save()

        invoice.status = CampaignInvoice.Status.PAID
        invoice.paid_at = timezone.now()
        invoice.save()

        # ۵. فعال‌سازی کمپین
        campaign = invoice.campaign
        campaign.status = Campaign.Status.ACTIVE
        campaign.save()

        # ۶. اعمال تغییرات (تمدید، افزایش خودرو، تغییر طراحی)
        PaymentService._apply_modifications(invoice)

        return {
            'message': 'پرداخت موفق بود',
            'ref_id': ref_id,
            'status': 'success'
        }

    @staticmethod
    def _apply_modifications(invoice):
        """اعمال تغییرات پس از پرداخت موفق"""
        if not invoice.modification_type:
            return

        campaign = invoice.campaign
        mod_data = invoice.modification_data

        if invoice.modification_type == 'EXTEND':
            new_end_date = datetime.fromisoformat(mod_data['new_end_date']).date()
            campaign.end_date = new_end_date
            campaign.save()
            campaign.setting.active_days += mod_data['additional_days']
            campaign.setting.save()

        elif invoice.modification_type == 'ADD_VEHICLES':
            campaign.setting.max_driver = mod_data['new_max_driver']
            campaign.setting.save()

        elif invoice.modification_type == 'CHANGE_DESIGN':
            new_design_data = mod_data['new_design']
            # Convert foreign key IDs to objects
            if new_design_data.get('template'):
                new_design_data['template'] = Template.objects.get(id=new_design_data['template'])
            if new_design_data.get('banner_type'):
                new_design_data['banner_type'] = BannerType.objects.get(id=new_design_data['banner_type'])
            CampaignDesignService.apply_changes(campaign, new_design_data)