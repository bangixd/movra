from rest_framework.exceptions import PermissionDenied
from campaigns.models import CampaignArea


class CampaignAreaService:
    """سرویس مدیریت محدودهٔ کمپین"""

    @staticmethod
    def get_queryset(user):
        """
        برگرداندن کوئری‌ست پایه با فیلترهای اختیاری
        """

        queryset = CampaignArea.objects.select_related(
            "campaign",
            "city",
            "neighborhood",
            "suggested_route",
        ).filter(campaign__client=user)

        # خواندن فیلترها از context (در ViewSet از request.query_params می‌آید)
        # اما در سرویس آن‌ها را به‌عنوان پارامتر دریافت می‌کنیم
        return queryset

    @staticmethod
    def apply_filters(queryset, filters: dict):
        """
        اعمال فیلترهای optional روی کوئری‌ست
        filters: dict با کلیدهای campaign_id, area_type, city_id, neighborhood_id
        """
        if filters.get('campaign_id'):
            queryset = queryset.filter(campaign_id=filters['campaign_id'])
        if filters.get('area_type'):
            queryset = queryset.filter(area_type=filters['area_type'])
        if filters.get('city_id'):
            queryset = queryset.filter(city_id=filters['city_id'])
        if filters.get('neighborhood_id'):
            queryset = queryset.filter(neighborhood_id=filters['neighborhood_id'])
        return queryset

    @staticmethod
    def validate_campaign_ownership(user, campaign):
        """
        بررسی مالکیت کمپین توسط کاربر
        Raises: PermissionDenied
        """
        if campaign.client.user.id != user.id:
            raise PermissionDenied("شما مجاز به استفاده از این کمپین نیستید.")

    @staticmethod
    def create_or_update_area(campaign, validated_data):
        """
        ایجاد یا به‌روزرسانی محدوده برای یک کمپین
        اگر محدوده‌ای از قبل وجود داشته باشد، آن را به‌روز می‌کند
        در غیر این صورت یک محدوده جدید می‌سازد

        Returns: (instance, created_flag)
        """
        existing = CampaignArea.objects.filter(campaign=campaign).first()
        if existing:
            for key, value in validated_data.items():
                setattr(existing, key, value)
            existing.save()
            return existing, False
        else:
            area = CampaignArea.objects.create(campaign=campaign, **validated_data)
            return area, True