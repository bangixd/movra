from django.db.models import Sum
from campaigns.models import Campaign, CampaignInvoice, CampaignPackage
from trips.models import TripAnalysis
from notifications.models import Notification
from campaigns.serializers import CampaignPackageSerializer


class ClientHomeService:
    """سرویس صفحهٔ اصلی (داشبورد) کلاینت"""

    @staticmethod
    def get_profile_info(client) -> dict:
        """اطلاعات بالای صفحه (پروفایل، موقعیت)"""
        return {
            'name': client.full_name,
            'city': client.city.name if client.city else None,
            'location': {
                'lat': client.location.y if client.location else None,
                'lng': client.location.x if client.location else None,
            } if client.location else None,
        }

    @staticmethod
    def get_packages():
        """پکیج‌های پیشنهادی فعال"""
        packages = CampaignPackage.objects.filter(is_active=True)
        return CampaignPackageSerializer(packages, many=True).data

    @staticmethod
    def get_my_campaigns(client) -> dict:
        """آخرین کمپین برای هر وضعیت (ACTIVE, COMPLETED, CANCELLED)"""
        statuses = [Campaign.Status.ACTIVE, Campaign.Status.COMPLETED, Campaign.Status.CANCELLED]
        result = {}

        for status in statuses:
            campaign = Campaign.objects.filter(
                client=client,  # campaign.client → ClientProfile
                status=status
            ).order_by('-created_at').first()

            if campaign:
                total_distance = TripAnalysis.objects.filter(
                    trip__campaign=campaign
                ).aggregate(d=Sum('distance_km'))['d'] or 0

                invoice = CampaignInvoice.objects.filter(
                    campaign=campaign,
                    status=CampaignInvoice.Status.PAID
                ).first()
                amount = float(invoice.total_price) if invoice else 0

                result[status] = {
                    'id': campaign.id,
                    'slogan': campaign.slogan,
                    'start_date': campaign.start_date,
                    'end_date': campaign.end_date,
                    'total_distance_km': total_distance,
                    'amount': amount,
                }
            else:
                result[status] = None

        return result

    @staticmethod
    def get_unread_notifications(user) -> int:
        """تعداد اعلان‌های خوانده‌نشده"""
        return Notification.objects.filter(recipient=user, is_read=False).count()

    @classmethod
    def get_home_data(cls, user) -> dict:
        """جمع‌آوری تمام داده‌های داشبورد"""
        client = user.client_profile

        return {
            'profile': cls.get_profile_info(client),
            'packages': cls.get_packages(),
            'my_campaigns': cls.get_my_campaigns(client),
            'unread_notifications': cls.get_unread_notifications(user),
        }