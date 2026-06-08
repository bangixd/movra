from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from campaigns.models import Campaign
from campaigns.services import CampaignReportService
from utils.permissions import IsClientUser


class CampaignAnalysisCSVView(APIView):
    """
    خروجی CSV گزارش تحلیل سفرهای یک کمپین.

    ### GET /campaigns/{campaign_id}/analysis/csv/
    فقط کلاینت صاحب کمپین یا ادمین می‌تواند دانلود کند.

    ### پاسخ:
    فایل CSV با ستون‌های: شناسه سفر، نام راننده، پلاک خودرو، عنوان کمپین،
    زمان شروع، زمان پایان، مدت فعال (ثانیه)، مسافت (کیلومتر)،
    امتیاز نمایش، تخمین تعداد مشاهده، درآمد (تومان)

    ### نکات:
    - فقط سفرهای کامل‌شده (COMPLETED) در خروجی قرار می‌گیرند.
    - فایل با BOM (کاراکتر \\ufeff) تولید می‌شود تا در Excel فارسی به‌هم نریزد.
    """
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request, campaign_id):
        # ۱. یافتن کمپین
        campaign = get_object_or_404(Campaign, id=campaign_id)

        # ۲. بررسی دسترسی
        try:
            CampaignReportService.check_access(request.user, campaign)
        except PermissionError as e:
            return Response({"error": str(e)}, status=403)

        # ۳. گرفتن تحلیل‌ها
        analyses = CampaignReportService.get_completed_trip_analyses(campaign)

        # ۴. تولید CSV
        csv_response = CampaignReportService.generate_csv_response(campaign, analyses)
        return csv_response