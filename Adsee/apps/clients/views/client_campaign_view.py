from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from clients.serializers import ClientCampaignSerializer
from clients.services import ClientCampaignService
from utils.permissions import IsClientUser


class ClientCampaignListView(ListAPIView):
    """
    لیست کمپین‌های کلاینت با قابلیت فیلتر.

    ### GET /clients/campaigns/
    پارامتر Query:
    - `status`: یکی از مقادیر `all` (پیش‌فرض)، `pending`، `active`، `completed`، `cancelled`

    ### نمونه پاسخ (خلاصه‌شده):
    ```json
    [
        {
            "id": 1,
            "slogan": "کمپین تست",
            "status": "ACTIVE",
            "start_date": "2026-01-01",
            "end_date": "2026-01-10"
        },
        ...
    ]
"""
    serializer_class = ClientCampaignSerializer
    permission_classes = [IsAuthenticated, IsClientUser]

    def get_queryset(self):
        client = self.request.user.client_profile
        status_filter = self.request.query_params.get('status', 'all')
        return ClientCampaignService.get_campaigns(client, status_filter)