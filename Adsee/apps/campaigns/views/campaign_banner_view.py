from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from campaigns.models import Campaign
from campaigns.services import CampaignBannerService
from utils.permissions import IsClientUser


class CampaignBannerImagesView(APIView):
    """
    نمایش تصاویر بنرهای نصب‌شدهٔ رانندگان برای یک کمپین.

    ### GET /campaigns/{campaign_id}/banner-images/
    فقط کلاینت صاحب کمپین می‌تواند ببیند.

    ### نمونه پاسخ:
    ```json
    [
        {
            "driver_name": "علی رضایی",
            "sticker_image": "https://movra.ir/media/stickers/abc.jpg",
            "driver_car_image": "https://movra.ir/media/cars/def.jpg"
        },
        ...
    ]
    نکات:
فقط تصاویری که sticker_image دارند برگردانده می‌شوند.
در صورت نبود تصویر، مقدار null برگردانده می‌شود.
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