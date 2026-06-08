from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from campaigns.models import Campaign
from campaigns.services import calculate_campaign_cost, CampaignValidationService
from utils.permissions import IsClientUser


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsClientUser])
def campaign_cost(request, campaign_id):
    """
    دریافت هزینهٔ تخمینی کمپین
    """
    # ۱. یافتن کمپین و بررسی مالکیت
    campaign = get_object_or_404(
        Campaign,
        id=campaign_id,
        brand_name__client__user=request.user
    )

    # ۲. بررسی تکمیل مراحل ضروری
    try:
        CampaignValidationService.ensure_required_steps_completed(campaign)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)

    # ۳. محاسبه و برگرداندن هزینه
    cost = calculate_campaign_cost(campaign)
    return Response(cost)