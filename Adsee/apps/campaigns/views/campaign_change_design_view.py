from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from campaigns.models import Campaign
from campaigns.serializers import CampaignDesignSerializer
from campaigns.services.campaign_service import CampaignService
from utils.permissions import IsClientUser


class CampaignChangeDesignView(APIView):
    """
    تغییر طراحی (بنر) کمپین
    """
    permission_classes = [IsAuthenticated, IsClientUser]

    def post(self, request, campaign_id):
        # ۱. یافتن کمپین و بررسی مالکیت
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            brand_name__client__user=request.user
        )

        # ۲. اعتبارسنجی داده‌های طراحی
        design_serializer = CampaignDesignSerializer(data=request.data)
        if not design_serializer.is_valid():
            return Response(design_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_design_data = design_serializer.validated_data

        # ۳. فراخوانی سرویس
        try:
            result = CampaignService.change_design(campaign, new_design_data)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)