from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from campaigns.models import Campaign
from campaigns.services.campaign_service import CampaignService
from utils.permissions import IsClientUser


class CampaignPauseView(APIView):
    """
    توقف یا ادامهٔ کمپین (Toggle Pause)
    """
    permission_classes = [IsAuthenticated, IsClientUser]

    def post(self, request, campaign_id):
        # ۱. یافتن کمپین و بررسی مالکیت
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            brand_name__client__user=request.user
        )

        # ۲. فراخوانی سرویس
        try:
            result = CampaignService.toggle_pause(campaign)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)