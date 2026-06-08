from rest_framework import generics, permissions
from trips.serializers import TripAnalysisSerializer
from campaigns.services import CampaignReportService


class CampaignAnalysisListView(generics.ListAPIView):
    """
    لیست تحلیل سفرهای یک کمپین خاص.

    ### GET /campaigns/{campaign_id}/analysis/
    فقط کلاینت صاحب کمپین یا ادمین می‌تواند ببیند.

    ### نمونه پاسخ:
    todo    بعد از تست api تحلیل اصلی باید ویرایش شود
    ```json
    [
        {
            "id": 1,
            "trip": 5,
            "active_seconds": 3600,
            "distance_km": 15.0,
            "exposure_score": 0.75,
            "estimated_impressions": 1200,
            "data_quality": 0.95,
            "confidence": 0.9,
            "avg_traffic_ratio": 1.1,
            "analysis_run_id": "run-001",
            "created_at": "2026-06-08T12:00:00Z"
        },
        ...
    ]
    """
    serializer_class = TripAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        campaign_id = self.kwargs.get('campaign_id')
        user = self.request.user
        return CampaignReportService.get_trip_analyses_for_campaign(campaign_id, user)