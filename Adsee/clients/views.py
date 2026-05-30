from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.throttling import UserRateThrottle
from rest_framework import viewsets, serializers, status
from rest_framework.permissions import IsAuthenticated
from .serializers import ClientProfileSerializer, ClientDocumentSerializer, ClientLocationSerializer
from .models import ClientProfile, ClientDocument
from campaigns.models import CampaignPackage, Campaign, CampaignInvoice, CampaignPricingRule
from campaigns.serializers import CampaignPackageSerializer, ClientCampaignSerializer
from notifications.models import Notification
from permissions import IsClientUser, IsClientOrAdmin, IsOwnerOrAdmin
from rest_framework.decorators import action, api_view, permission_classes
from django.contrib.gis.geos import Point
from services.neshan_client import NeshanClient
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from trips.models import TripAnalysis, HourlyActivity, Trip
from django.utils import timezone
from rest_framework.generics import ListAPIView


class ClientProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin, IsOwnerOrAdmin]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    def get_queryset(self):
        if self.request.user.is_staff:
            return ClientProfile.objects.all()
        return ClientProfile.objects.filter(user=self.request.user)

    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'POST':
            try:
                kwargs['data']['user'] = self.request.user.pk
            except:
                pass
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)


    def perform_create(self, serializer):
        # اگر در درخواست، user مشخص شده باشد، از آن استفاده کن
        user_id = self.request.data.get('user')
        if user_id:
            try:
                user = get_object_or_404(get_user_model(), pk=user_id)
                serializer.save(user=user)
            except ValueError:  # اگر user_id عدد نباشد
                raise serializers.ValidationError({"user": "شناسه کاربر نامعتبر است."})
        else:
            # اگر user مشخص نشده باشد، باید خطا بدهد (چون برای ادمین هم الزامی است)
            raise serializers.ValidationError({"user": "شناسه کاربر الزامی است."})


    @action(detail=False, methods=['post'], url_path='set-location')
    def set_location(self, request):
        serializer = ClientLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data['lat']
        lng = serializer.validated_data['lng']
        point = Point(lng, lat, srid=4326)

        profile = self.get_queryset().first()
        if not profile:
            return Response({"error": "پروفایلی یافت نشد"}, status=404)

        profile.location = point
        profile.save(update_fields=['location'])

        return Response({
            "message": "موقعیت مکانی با موفقیت ذخیره شد",
            "location": {
                "lat": lat,
                "lng": lng
            }
        })

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def my_profile(self, request):
        profile = self.get_queryset().first()
        if not profile:
            return Response({"error": "پروفایلی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

class ClientHomeView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request):
        user = request.user
        client = user.client_profile

        # ۱. اطلاعات بالای صفحه
        profile = {
            'name': client.full_name,
            'city': client.city.name if client.city else None,
            'location': {
                'lat': client.location.y if client.location else None,
                'lng': client.location.x if client.location else None,
            } if client.location else None,
        }

        # ۲. پکیج‌های پیشنهادی
        packages = CampaignPackage.objects.filter(is_active=True)
        package_data = CampaignPackageSerializer(packages, many=True).data

        # ۳. کمپین‌های من (آخرین هر وضعیت)
        statuses = [Campaign.Status.ACTIVE, Campaign.Status.COMPLETED, Campaign.Status.CANCELLED]
        my_campaigns = {}
        for status in statuses:
            campaign = Campaign.objects.filter(
                brand_name__client=client,
                status=status
            ).order_by('-created_at').first()
            if campaign:
                # اطلاعات تکمیلی
                total_distance = TripAnalysis.objects.filter(
                    trip__campaign=campaign
                ).aggregate(d=Sum('distance_km'))['d'] or 0

                # مبلغ (از فاکتور پرداخت‌شده یا هزینهٔ فعلی)
                invoice = CampaignInvoice.objects.filter(
                    campaign=campaign,
                    status=CampaignInvoice.Status.PAID
                ).first()
                amount = float(invoice.total_price) if invoice else 0

                my_campaigns[status] = {
                    'id': campaign.id,
                    'slogan': campaign.slogan,
                    'start_date': campaign.start_date,
                    'end_date': campaign.end_date,
                    'total_distance_km': total_distance,
                    'amount': amount,
                }
            else:
                my_campaigns[status] = None

        # ۴. اعلان‌ها
        unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()

        return Response({
            'profile': profile,
            'packages': package_data,
            'my_campaigns': my_campaigns,
            'unread_notifications': unread_notifications,
        })

class ClientDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = ClientDocumentSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return ClientDocument.objects.all()
        return ClientDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def review(self, request, pk=None):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        doc = self.get_object()
        new_status = request.data.get('status')
        if new_status not in [ClientDocument.ApprovalStatus.APPROVED, ClientDocument.ApprovalStatus.REJECTED]:
            return Response({"error": "invalid status"}, status=400)

        doc.status = new_status
        doc.reviewed_at = timezone.now()
        if new_status == ClientDocument.ApprovalStatus.REJECTED:
            doc.reject_reason = request.data.get('reject_reason', '')
        doc.save()
        return Response(ClientDocumentSerializer(doc).data)

class ClientReportSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request):
        user = request.user
        client = user.client_profile
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # کمپین‌های این کلاینت
        campaigns = Campaign.objects.filter(brand_name__client=client)
        if start_date:
            campaigns = campaigns.filter(start_date__gte=start_date)
        if end_date:
            campaigns = campaigns.filter(end_date__lte=end_date)

        total_campaigns = campaigns.count()

        # مجموع ساعات فعال (از تحلیل سفرها)
        total_active_seconds = TripAnalysis.objects.filter(
            trip__campaign__in=campaigns,
            trip__status='COMPLETED'
        ).aggregate(total=Sum('active_seconds'))['total'] or 0
        total_hours = round(total_active_seconds / 3600, 1)

        # مجموع هزینه‌های پرداخت‌شده
        total_cost = CampaignInvoice.objects.filter(
            campaign__in=campaigns,
            status=CampaignInvoice.Status.PAID
        ).aggregate(total=Sum('total_price'))['total'] or 0

        # مجموع روزهای فعال (از تنظیمات کمپین‌ها)
        total_days = campaigns.aggregate(total=Sum('setting__active_days'))['total'] or 0

        return Response({
            'total_campaigns': total_campaigns,
            'total_hours_seen': total_hours,
            'total_cost': float(total_cost),
            'total_days': total_days,
        })

class ClientPeakHoursView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request):
        user = request.user
        client = user.client_profile
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # فیلتر کمپین‌های کلاینت
        campaigns = Campaign.objects.filter(brand_name__client=client)
        if start_date:
            campaigns = campaigns.filter(start_date__gte=start_date)
        if end_date:
            campaigns = campaigns.filter(end_date__lte=end_date)

        # سفرهای تکمیل‌شدهٔ این کمپین‌ها
        trips = Trip.objects.filter(
            campaign__in=campaigns,
            status=Trip.Status.COMPLETED
        )

        # چک کنیم آیا داده‌های HourlyActivity وجود دارد؟
        has_hourly_data = HourlyActivity.objects.filter(trip__in=trips).exists()

        hourly_activity = [0] * 24
        if has_hourly_data:
            # تجمیع از روی HourlyActivity
            aggregates = HourlyActivity.objects.filter(trip__in=trips).values('hour').annotate(
                total_seconds=Sum('active_seconds')
            )
            for agg in aggregates:
                hourly_activity[agg['hour']] = agg['total_seconds']
        else:
            # روش تقریبی (همانطور که قبلاً بود)
            analyses = TripAnalysis.objects.filter(trip__in=trips)
            for analysis in analyses:
                if analysis.active_seconds > 0:
                    per_hour = analysis.active_seconds / 24.0
                    for i in range(24):
                        hourly_activity[i] += per_hour

        chart_data = [
            {'hour': h, 'seconds': round(hourly_activity[h], 1)}
            for h in range(24)
        ]

        return Response({'chart_data': chart_data})

class BillboardComparisonView(APIView):
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request):
        user = request.user
        client = user.client_profile
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        campaigns = Campaign.objects.filter(brand_name__client=client)
        if start_date:
            campaigns = campaigns.filter(start_date__gte=start_date)
        if end_date:
            campaigns = campaigns.filter(end_date__lte=end_date)

        # مجموع تخمین نمایش‌ها
        total_impressions = TripAnalysis.objects.filter(
            trip__campaign__in=campaigns,           # استفاده از کمپین‌های فیلترشده
            trip__status=Trip.Status.COMPLETED
        ).aggregate(total=Sum('estimated_impressions'))['total'] or 0

        # خواندن عدد مبنا از قوانین (مثلاً کلید BILLBOARD_DAILY_IMPRESSIONS)
        rule = CampaignPricingRule.objects.filter(key='BILLBOARD_DAILY_IMPRESSIONS', is_active=True).first()
        billboard_impressions = rule.value if rule else 50000  # پیش‌فرض ۵۰ هزار

        # مقایسه
        ratio = round(total_impressions / billboard_impressions, 2) if billboard_impressions > 0 else 0

        return Response({
            'our_total_impressions': total_impressions,
            'billboard_daily_impressions': billboard_impressions,
            'ratio': ratio,
            'message': f'تأثیر تبلیغات شما معادل {ratio} روز نمایش بیلبورد است.'
        })

class ClientCampaignListView(ListAPIView):
    serializer_class = ClientCampaignSerializer
    permission_classes = [IsAuthenticated, IsClientUser]

    def get_queryset(self):
        user = self.request.user
        client = user.client_profile
        queryset = Campaign.objects.filter(brand_name__client=client)

        status_filter = self.request.query_params.get('status', 'all')
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

        return queryset.order_by('-created_at')

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsClientUser])
def reverse_geocode(request):
    lat = request.data.get('lat')
    lng = request.data.get('lng')

    if not lat or not lng:
        return Response(
            {'error': 'عرض و طول جغرافیایی الزامی است'},
            status=status.HTTP_400_BAD_REQUEST
        )

    client = NeshanClient()
    result = client.reverse_geocode(lat, lng)

    if result:
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': 'دریافت آدرس با خطا مواجه شد'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
