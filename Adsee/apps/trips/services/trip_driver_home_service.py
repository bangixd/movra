from datetime import date
from campaigns.models import Campaign
from campaigns.serializers import AvailableCampaignSerializer
from trips.models import Trip
from trips.serializers import DriverTripDetailSerializer
from geo.models import DriverLocation
from notifications.models import Notification


class DriverHomeService:
    """سرویس صفحهٔ اصلی (داشبورد) راننده"""

    @staticmethod
    def get_profile_data(user):
        driver = user.driver_profile
        data = {
            'name': driver.full_name,
            'avatar': driver.avatar.url if driver.avatar else None,
            'wallet_balance': user.wallet.balance,
            'kyc_status': driver.kyc_status,
        }
        last_location = DriverLocation.objects.filter(driver=user).order_by('-timestamp').first()
        if last_location:
            data['last_location'] = {
                'lat': last_location.point.y,
                'lng': last_location.point.x,
                'timestamp': last_location.timestamp.isoformat()
            }
        return data

    @staticmethod
    def get_dashboard_data(user):
        profile = DriverHomeService.get_profile_data(user)
        driver = user.driver_profile

        active_trip = Trip.objects.filter(
            driver=driver,
            status__in=[Trip.Status.ACTIVE, Trip.Status.PAUSED]
        ).select_related('campaign', 'vehicle', 'campaign__area', 'campaign__design__print_shop').first()

        if active_trip:
            trip_serializer = DriverTripDetailSerializer(active_trip)
            campaign_data = None
            status = 'active_trip'
        else:
            city = driver.city
            available = Campaign.objects.filter(
                status=Campaign.Status.ACTIVE,
                start_date__lte=date.today(),
                end_date__gte=date.today()
            )
            if city:
                available = available.filter(area__city=city)
            campaign_serializer = AvailableCampaignSerializer(available, many=True)
            campaign_data = campaign_serializer.data
            trip_serializer = None
            status = 'no_active_trip'

        unread = Notification.objects.filter(recipient=user, is_read=False).count()

        return {
            'profile': profile,
            'status': status,
            'active_trip': trip_serializer.data if trip_serializer else None,
            'available_campaigns': campaign_data,
            'unread_notifications': unread,
        }