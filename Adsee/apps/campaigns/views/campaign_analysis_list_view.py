from rest_framework import generics, permissions
from trips.serializers import TripAnalysisSerializer
from campaigns.services import CampaignReportService


class CampaignAnalysisListView(generics.ListAPIView):
    """
    لیست تحلیل سفرهای یک کمپین خاص.
    فقط کلاینت صاحب کمپین یا ادمین می‌تواند ببیند.
    """
    serializer_class = TripAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        campaign_id = self.kwargs.get('campaign_id')
        user = self.request.user
        return CampaignReportService.get_trip_analyses_for_campaign(campaign_id, user)