from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from campaigns.models import Campaign
from campaigns.services import CampaignReportService
from utils.permissions import IsClientUser


class CampaignAnalysisCSVView(APIView):
    """
    خروجی CSV گزارش تحلیل سفرهای یک کمپین
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