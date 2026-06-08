from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from campaigns.models import Campaign
from campaigns.services.campaign_service import CampaignService
from utils.permissions import IsClientUser


class CampaignExtendView(APIView):
    """
    تمدید مدت کمپین
    """
    permission_classes = [IsAuthenticated, IsClientUser]

    def post(self, request, campaign_id):
        # 1. Find the campaign & verify ownership
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            brand_name__client__user=request.user
        )

        # 2. Validate additional_days
        additional_days = request.data.get('days')
        if not additional_days:
            return Response(
                {"error": "تعداد روز تمدید الزامی است"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            additional_days = int(additional_days)
            if additional_days <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {"error": "تعداد روز باید یک عدد صحیح مثبت باشد"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Call the service
        try:
            result = CampaignService.extend(campaign, additional_days)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)