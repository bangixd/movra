from campaigns.models import Campaign


class ClientCampaignService:
    """Service for listing client campaigns"""

    @staticmethod
    def get_campaigns(client, status_filter='all'):
        """
        Return campaigns for a client, optionally filtered by status.

        Args:
            client: ClientProfile instance
            status_filter: 'all', 'pending', 'active', 'completed', 'cancelled'

        Returns:
            QuerySet of Campaign
        """
        queryset = Campaign.objects.filter(client=client)

        if status_filter == 'pending':
            queryset = queryset.filter(status__in=[
                Campaign.Status.DRAFT,
                Campaign.Status.WAITING_FOR_DESIGN,
                Campaign.Status.WAITING_FOR_PAYMENT
            ])
        elif status_filter == 'active':
            queryset = queryset.filter(status__in=[
                Campaign.Status.ACTIVE,
                Campaign.Status.PAUSED
            ])
        elif status_filter == 'completed':
            queryset = queryset.filter(status=Campaign.Status.COMPLETED)
        elif status_filter == 'cancelled':
            queryset = queryset.filter(status=Campaign.Status.REJECTED)
        # else: 'all' → no filter

        return queryset.order_by('-created_at')