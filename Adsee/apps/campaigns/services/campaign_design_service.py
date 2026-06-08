from campaigns.models import CampaignDesign


class CampaignDesignService:
    """سرویس مدیریت طراحی کمپین"""

    @staticmethod
    def apply_changes(campaign, new_design_data: dict) -> CampaignDesign:
        """
        اعمال تغییرات طراحی روی کمپین
        اگر طراحی وجود داشته باشد ← ویرایش
        در غیر این صورت ← ایجاد
        Returns: نمونهٔ CampaignDesign
        """
        if hasattr(campaign, 'design'):
            design = campaign.design
            for key, value in new_design_data.items():
                setattr(design, key, value)
            design.save()
            return design
        else:
            return CampaignDesign.objects.create(campaign=campaign, **new_design_data)

    @staticmethod
    def get_old_design_cost(campaign) -> dict:
        """
        استخراج داده‌های طراحی قدیم برای محاسبهٔ مابه‌التفاوت
        Returns: dict با کلیدهای design_type, template, banner_type
        """
        if not hasattr(campaign, 'design'):
            return None

        design = campaign.design
        return {
            'design_type': design.design_type,
            'template': design.template_id,
            'banner_type': design.banner_type_id,
        }

    @staticmethod
    def get_queryset(user):
        """
        Return the base queryset for CampaignDesign, filtered by user.
        - Admin: all designs
        - Client: only designs of their own campaigns
        """
        qs = CampaignDesign.objects.select_related('campaign', 'template').all()

        if not user.is_authenticated:
            return qs.none()

        if user.is_staff:
            return qs

        return qs.filter(campaign__client=user)

    @staticmethod
    def get_serializer_class(action: str):
        """
        Return the appropriate serializer class based on the action.
        """
        from campaigns.serializers import (
            CampaignDesignSerializer,
            CampaignDesignCreateSerializer,
            CampaignDesignUpdateSerializer,
        )

        if action == 'create':
            return CampaignDesignCreateSerializer
        elif action in ['update', 'partial_update']:
            return CampaignDesignUpdateSerializer
        return CampaignDesignSerializer