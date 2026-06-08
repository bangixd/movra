from rest_framework.viewsets import ModelViewSet
from campaigns.services.campaign_design_service import CampaignDesignService
from utils.permissions import IsClientUser, IsOwnerOrAdmin


class CampaignDesignViewSet(ModelViewSet):
    """
    مدیریت طراحی‌های کمپین
    """
    permission_classes = [IsClientUser, IsOwnerOrAdmin]

    def get_queryset(self):
        return CampaignDesignService.get_queryset(self.request.user)

    def get_serializer_class(self):
        return CampaignDesignService.get_serializer_class(self.action)