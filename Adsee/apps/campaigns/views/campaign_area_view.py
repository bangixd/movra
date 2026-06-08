from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from campaigns.models import CampaignArea
from campaigns.serializers import CampaignAreaDetailSerializer, CampaignAreaCreateSerializer
from campaigns.services.campaign_area_service import CampaignAreaService
from utils.permissions import IsClientUser, IsOwnerOrAdmin


class CampaignAreaViewSet(ModelViewSet):
    """مدیریت محدودهٔ کمپین"""
    permission_classes = [IsClientUser, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return CampaignArea.objects.none()

        # گرفتن کوئری‌ست پایه
        queryset = CampaignAreaService.get_queryset(user)

        # اعمال فیلترها از query params
        filters = {
            'campaign_id': self.request.query_params.get("campaign"),
            'area_type': self.request.query_params.get("area_type"),
            'city_id': self.request.query_params.get("city"),
            'neighborhood_id': self.request.query_params.get("neighborhood"),
        }
        return CampaignAreaService.apply_filters(queryset, filters)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return CampaignAreaDetailSerializer
        return CampaignAreaCreateSerializer

    def perform_create(self, serializer):
        campaign = serializer.validated_data.get("campaign")
        CampaignAreaService.validate_campaign_ownership(self.request.user, campaign)
        serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        CampaignAreaService.validate_campaign_ownership(self.request.user, instance.campaign)

        # اگر کمپین در حال تغییر است، مالکیت کمپین جدید را هم چک کن
        new_campaign = serializer.validated_data.get("campaign", instance.campaign)
        if new_campaign != instance.campaign:
            CampaignAreaService.validate_campaign_ownership(self.request.user, new_campaign)
        serializer.save()

    def perform_destroy(self, instance):
        CampaignAreaService.validate_campaign_ownership(self.request.user, instance.campaign)
        instance.delete()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        campaign = serializer.validated_data.get("campaign")
        CampaignAreaService.validate_campaign_ownership(request.user, campaign)

        # ایجاد یا به‌روزرسانی
        area, created = CampaignAreaService.create_or_update_area(
            campaign,
            serializer.validated_data
        )

        output_serializer = CampaignAreaDetailSerializer(
            area,
            context=self.get_serializer_context()
        )
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )