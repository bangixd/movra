from campaigns.models import CampaignDesign


class PrintShopDesignService:
    """سرویس مدیریت طرح‌های ارجاع‌شده به چاپخانه"""

    @staticmethod
    def get_assigned_designs(user):
        """
        برگرداندن طرح‌هایی که به چاپخانهٔ فعلی ارجاع شده‌اند.
        """
        return CampaignDesign.objects.filter(print_shop__user=user)

    @staticmethod
    def get_design_for_printshop(design_id, user) -> CampaignDesign:
        """
        یافتن طرحی که به چاپخانهٔ فعلی ارجاع شده است.
        Raises: CampaignDesign.DoesNotExist اگر طرح یافت نشد یا متعلق به چاپخانه نباشد
        """
        return CampaignDesign.objects.get(
            id=design_id,
            print_shop__user=user
        )

    @staticmethod
    def update_print_status(design: CampaignDesign, print_status: str = None, estimated_ready_date: str = None) -> CampaignDesign:
        """
        به‌روزرسانی وضعیت چاپ و تاریخ آماده‌سازی.
        Args:
            design: نمونهٔ طراحی
            print_status: وضعیت چاپ جدید (PENDING, ACCEPTED, IN_PROGRESS, READY, DELIVERED, REJECTED)
            estimated_ready_date: تاریخ تخمینی آماده‌سازی
        Returns:
            نمونهٔ به‌روزرسانی‌شده
        """
        if print_status:
            design.print_status = print_status
        if estimated_ready_date:
            design.estimated_ready_date = estimated_ready_date
        design.save()
        return design