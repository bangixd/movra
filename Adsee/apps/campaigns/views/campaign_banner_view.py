from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from campaigns.models import Campaign
from campaigns.services import CampaignBannerService
from utils.permissions import IsClientUser


class CampaignBannerImagesView(APIView):
    """
    نمایش تصاویر بنرهای نصب‌شده رانندگان برای یک کمپین
    """
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request, campaign_id):
        # ۱. یافتن کمپین و بررسی مالکیت
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            brand_name__client__user=request.user
        )

        # ۲. گرفتن تصاویر از سرویس
        images = CampaignBannerService.get_banner_images(campaign, request=request)

        return Response(images)