from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from campaigns.models import CampaignPackage
from campaigns.serializers import CampaignPackageSerializer
from utils.permissions import IsClientUser, IsOwnerOrAdmin

class CampaignPackageListView(ListAPIView):
    queryset = CampaignPackage.objects.filter(is_active=True)
    serializer_class = CampaignPackageSerializer
    permission_classes = [IsAuthenticated, IsClientUser]
