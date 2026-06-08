from campaigns.models import Campaign, PaymentTransaction, CampaignInvoice
from campaigns.services.pricing import calculate_campaign_cost, get_rule_value
from decimal import Decimal
from datetime import timedelta
from campaigns.services.design_cost_service import DesignCostService
from campaigns.services.campaign_design_service import CampaignDesignService
from campaigns.services.invoice_service import InvoiceService
from services.payment_gateway import ZarinpalGateway


class CampaignService:
    """سرویس مدیریت کمپین (عملیات خاص)"""
    # Validation
    @staticmethod
    def validate_can_modify(campaign) -> None:
        """
        بررسی امکان تغییرات کمپین
        Raises: ValueError در صورت عدم امکان
        """
        allowed_statuses = [
            Campaign.Status.ACTIVE,
            Campaign.Status.PAUSED,
            Campaign.Status.DRAFT,
        ]
        if campaign.status not in allowed_statuses:
            raise ValueError("در وضعیت فعلی امکان این عملیات وجود ندارد")

    # Operations
    @staticmethod
    def add_vehicles(campaign, additional_vehicles: int) -> dict:
        """
        افزایش تعداد خودروهای کمپین
        Args:
            campaign: کمپین
            additional_vehicles: تعداد خودروی اضافی (عدد صحیح مثبت)
        Returns:
            dict: {'payment_url': ..., 'invoice_id': ..., 'extra_amount': ..., 'total': ...}
        Raises:
            ValueError: در صورت عدم امکان تغییر
            ConnectionError: در صورت خطا در اتصال به درگاه
        """
        # ۱. اعتبارسنجی وضعیت کمپین
        CampaignService.validate_can_modify(campaign)

        # ۲. محاسبهٔ هزینه
        per_vehicle_cost = get_rule_value('DRIVER_COST_PER_DAY', Decimal('200000')) * campaign.setting.active_days
        extra_amount = Decimal(per_vehicle_cost * additional_vehicles)

        # ۳. ایجاد فاکتور
        invoice = InvoiceService.create_modification_invoice(
            campaign=campaign,
            modification_type='ADD_VEHICLES',
            extra_amount=extra_amount,
            modification_data={
                'additional_vehicles': additional_vehicles,
                'new_max_driver': campaign.setting.max_driver + additional_vehicles,
                'extra_amount': float(extra_amount),
            },
            snapshot_extra={
                'additional_vehicles': additional_vehicles,
            }
        )

        # ۴. اتصال به درگاه پرداخت
        gateway = ZarinpalGateway()
        success, payment_url_or_error, error = gateway.send_request(
            amount=invoice.total_price,
            description=f'افزایش خودرو کمپین {campaign.slogan}',
            mobile=campaign.client.user.phone
        )

        if not success:
            # اگر درگاه خطا داد، فاکتور را باطل کن
            invoice.status = CampaignInvoice.Status.VOID
            invoice.save()
            raise ConnectionError(error or "خطا در اتصال به درگاه پرداخت")

        # ۵. ثبت تراکنش
        PaymentTransaction.objects.create(
            invoice=invoice,
            authority=payment_url_or_error.split('/')[-1],
            amount=invoice.total_price,
            status=PaymentTransaction.Status.INITIATED
        )

        return {
            'payment_url': payment_url_or_error,
            'invoice_id': invoice.id,
            'extra_amount': float(extra_amount),
            'total': float(invoice.total_price),
        }

    @staticmethod
    def change_design(campaign, new_design_data: dict) -> dict:
        """
        تغییر طراحی کمپین (با امکان پرداخت مابه‌التفاوت)
        Args:
            campaign: کمپین
            new_design_data: داده‌های طراحی جدید
        Returns:
            dict: نتیجهٔ عملیات (شامل payment_url در صورت نیاز به پرداخت)
        Raises:
            ValueError: در صورت عدم امکان تغییر
            ConnectionError: در صورت خطا در درگاه
        """
        # ۱. اعتبارسنجی وضعیت کمپین
        allowed_statuses = [
            Campaign.Status.DRAFT,
            Campaign.Status.ACTIVE,
            Campaign.Status.PAUSED,
        ]
        if campaign.status not in allowed_statuses:
            raise ValueError("در وضعیت فعلی امکان تغییر بنر وجود ندارد")

        # ۲. محاسبهٔ هزینهٔ طراحی جدید
        new_design_cost = DesignCostService.calculate(new_design_data)

        # ۳. محاسبهٔ هزینهٔ طراحی قدیم
        old_design_cost = Decimal('0')
        old_design_data = CampaignDesignService.get_old_design_cost(campaign)
        if old_design_data:
            old_design_cost = DesignCostService.calculate(old_design_data)

        # ۴. مابه‌التفاوت
        extra_amount = Decimal(new_design_cost - old_design_cost)

        # ۵. اگر مابه‌التفاوت صفر یا منفی است ← بدون پرداخت اعمال کن
        if extra_amount <= 0:
            CampaignDesignService.apply_changes(campaign, new_design_data)
            return {
                "message": "تغییرات طراحی با موفقیت اعمال شد",
                "paid": False
            }

        # ۶. ایجاد فاکتور برای مابه‌التفاوت
        invoice = InvoiceService.create_modification_invoice(
            campaign=campaign,
            modification_type='CHANGE_DESIGN',
            extra_amount=extra_amount,
            modification_data={
                'new_design': new_design_data,
                'new_design_cost': float(new_design_cost),
                'old_design_cost': float(old_design_cost),
                'extra_amount': float(extra_amount),
            },
        )

        # ۷. اتصال به درگاه
        gateway = ZarinpalGateway()
        success, payment_url_or_error, error = gateway.send_request(
            amount=invoice.total_price,
            description=f'تغییر بنر کمپین {campaign.slogan}',
            mobile=campaign.client.user.phone
        )

        if not success:
            invoice.status = CampaignInvoice.Status.VOID
            invoice.save()
            raise ConnectionError(error or "خطا در اتصال به درگاه پرداخت")

        # ۸. ثبت تراکنش
        PaymentTransaction.objects.create(
            invoice=invoice,
            authority=payment_url_or_error.split('/')[-1],
            amount=invoice.total_price,
            status=PaymentTransaction.Status.INITIATED
        )

        return {
            'payment_url': payment_url_or_error,
            'invoice_id': invoice.id,
            'extra_amount': float(extra_amount),
            'total': float(invoice.total_price),
        }

    @staticmethod
    def extend(campaign, additional_days: int) -> dict:
        """
        Extend a campaign by a number of days.
        Args:
            campaign: the Campaign instance
            additional_days: positive integer
        Returns:
            dict: {'payment_url': ..., 'invoice_id': ..., 'extra_amount': ..., 'total': ...}
        Raises:
            ValueError: if campaign status doesn't allow extension
            ConnectionError: if payment gateway fails
        """
        # 1. Validate campaign status
        allowed_statuses = [
            Campaign.Status.ACTIVE,
            Campaign.Status.PAUSED,
            Campaign.Status.DRAFT,
        ]
        if campaign.status not in allowed_statuses:
            raise ValueError("در وضعیت فعلی امکان تمدید کمپین وجود ندارد")

        # 2. Calculate the cost
        base_cost = calculate_campaign_cost(campaign)
        daily_vehicle_driver_cost = (
            base_cost['vehicle'] + base_cost['driver']
        ) / campaign.setting.active_days
        extra_amount = Decimal(daily_vehicle_driver_cost * additional_days)

        # 3. Create the invoice
        new_end_date = campaign.end_date + timedelta(days=additional_days) if campaign.end_date else None
        invoice = InvoiceService.create_modification_invoice(
            campaign=campaign,
            modification_type='EXTEND',
            extra_amount=extra_amount,
            modification_data={
                'additional_days': additional_days,
                'new_end_date': new_end_date.isoformat() if new_end_date else None,
                'extra_amount': float(extra_amount),
            },
        )

        # 4. Connect to payment gateway
        gateway = ZarinpalGateway()
        success, payment_url_or_error, error = gateway.send_request(
            amount=invoice.total_price,
            description=f'تمدید کمپین {campaign.slogan}',
            mobile=campaign.client.user.phone
        )

        if not success:
            invoice.status = CampaignInvoice.Status.VOID
            invoice.save()
            raise ConnectionError(error or "خطا در اتصال به درگاه پرداخت")

        # 5. Record the transaction
        PaymentTransaction.objects.create(
            invoice=invoice,
            authority=payment_url_or_error.split('/')[-1],
            amount=invoice.total_price,
            status=PaymentTransaction.Status.INITIATED
        )

        return {
            'payment_url': payment_url_or_error,
            'invoice_id': invoice.id,
            'extra_amount': float(extra_amount),
            'total': float(invoice.total_price),
        }

    @staticmethod
    def toggle_pause(campaign) -> dict:
        """
        تغییر وضعیت کمپین بین ACTIVE و PAUSED
        Args:
            campaign: نمونهٔ کمپین
        Returns:
            dict: {'status': وضعیت جدید}
        Raises:
            ValueError: اگر وضعیت کمپین اجازهٔ توقف/ادامه ندهد
        """
        if campaign.status not in [Campaign.Status.ACTIVE, Campaign.Status.PAUSED]:
            raise ValueError("وضعیت کمپین اجازهٔ توقف یا ادامه نمی‌دهد")

        # تغییر وضعیت
        new_status = Campaign.Status.PAUSED if campaign.status == Campaign.Status.ACTIVE else Campaign.Status.ACTIVE
        campaign.status = new_status
        campaign.save()

        return {"status": new_status}

    # Basic CRUD
    @staticmethod
    def get_queryset(user):
        """
        Return campaigns based on user role.
        - Admin: all non-deleted campaigns
        - Client: only their own non-deleted campaigns
        """
        if not user.is_authenticated:
            return Campaign.objects.none()
        if user.is_staff:
            return Campaign.objects.filter(is_deleted=False)
        return Campaign.objects.filter(
            is_deleted=False,
            client__user=user
        )

    @staticmethod
    def create_campaign(user, validated_data: dict) -> Campaign:
        """
        Create a new campaign for a client.
        Args:
            user: the authenticated user (must have client_profile)
            validated_data: serializer validated data
        Returns:
            the created Campaign instance
        Raises:
            AttributeError: if user has no client_profile
        """
        if not hasattr(user, 'client_profile'):
            raise ValueError("User does not have a client profile.")
        validated_data['client'] = user.client_profile
        return Campaign.objects.create(**validated_data)