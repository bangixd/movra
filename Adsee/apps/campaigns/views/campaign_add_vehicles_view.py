from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from campaigns.models import Campaign
from campaigns.services.campaign_service import CampaignService
from utils.permissions import IsClientUser


class CampaignAddVehiclesView(APIView):
    """
    افزایش تعداد خودروهای کمپین
    """
    permission_classes = [IsAuthenticated, IsClientUser]

    def post(self, request, campaign_id):
        # ۱. یافتن کمپین و بررسی مالکیت
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            brand_name__client__user=request.user
        )

        # ۲. اعتبارسنجی تعداد خودرو
        additional_vehicles = request.data.get('count')
        if not additional_vehicles:
            return Response(
                {"error": "تعداد خودروی اضافی الزامی است"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            additional_vehicles = int(additional_vehicles)
            if additional_vehicles <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {"error": "تعداد باید یک عدد صحیح مثبت باشد"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ۳. فراخوانی سرویس
        try:
            result = CampaignService.add_vehicles(campaign, additional_vehicles)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)