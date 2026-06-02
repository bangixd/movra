from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
from datetime import date
import csv
from django.utils import timezone
from .models import Trip, TripAnalysis
from .serializers import (
    TripCreateSerializer,
    TripListSerializer,
    TripDetailSerializer,
    TripStatusUpdateSerializer,
    TripAnalysisSerializer,
    DriverTripListSerializer,
    DriverTripDetailSerializer,
    InstallationUploadSerializer,
)
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from campaigns.models import Campaign
from campaigns.serializers import CampaignBriefSerializer, AvailableCampaignSerializer
from permissions import IsDriverUser, IsClientUser
from services.tasks import update_earnings_task, fetch_and_store_trip_analysis
from services.analytics_client import AnalyticsServiceClient
from geo.models import DriverLocation
from notifications.models import Notification
import logging


logger = logging.getLogger(__name__)
class TripFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Trip.Status.choices)

    class Meta:
        model = Trip
        fields = ['status']

class TripViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsDriverUser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TripFilter

    def get_serializer_class(self):
        if self.action == 'create':
            return TripCreateSerializer
        elif self.action in ['start', 'pause', 'resume', 'complete', 'cancel']:
            return TripStatusUpdateSerializer
        if self.action == 'list':
            return DriverTripListSerializer
        elif self.action == 'retrieve':
            return DriverTripDetailSerializer
        return TripDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Trip.objects.none()
        if user.is_staff:
            return Trip.objects.all()
        # راننده فقط سفرهای خودش را ببیند
        return Trip.objects.filter(driver__user=user)

    @action(detail=False, methods=['get'], url_path='available-campaigns')
    def available_campaigns(self, request):
        now = timezone.now()
        campaigns = Campaign.objects.filter(
            status=Campaign.Status.ACTIVE,
            created_at__lte=now,
        )
        print("Found campaigns:", campaigns.count())
        city_id = request.query_params.get('city_id')
        if city_id:
            try:
                city_id = int(city_id)
            except (TypeError, ValueError):
                return Response({"error": "city_id نامعتبر است."},
                                status=status.HTTP_400_BAD_REQUEST)
            campaigns = campaigns.filter(area__city__id=city_id)
            print(campaigns, city_id)
        serializer = CampaignBriefSerializer(campaigns, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        trip = Trip.objects.filter(
            driver__user=request.user
        ).exclude(
            status__in=[Trip.Status.COMPLETED, Trip.Status.CANCELLED]
        ).first()
        if trip:
            return Response(TripDetailSerializer(trip).data)
        return Response({"detail": "سفر فعالی ندارید."},
                        status=status.HTTP_404_NOT_FOUND)

    # --- اکشن‌های تغییر وضعیت (همه با بررسی user_id) ---
    @action(detail=True, methods=['patch'])
    def start(self, request, pk=None):
        trip = self.get_object()
        if trip.driver.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status != Trip.Status.PENDING:
            return Response({"error": "فقط سفرهای در انتظار می‌توانند شروع شوند."},
                            status=status.HTTP_400_BAD_REQUEST)
        # if not trip.installation_verified:
            # return Response({"error": "ابتدا باید عکس‌های نصب بنر تأیید شوند."}, status=400)
        trip.status = Trip.Status.ACTIVE
        trip.start_time = timezone.now()
        trip.save()
        return Response(TripDetailSerializer(trip).data)

    @action(detail=True, methods=['patch'])
    def pause(self, request, pk=None):
        trip = self.get_object()
        if trip.driver.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status != Trip.Status.ACTIVE:
            return Response({"error": "فقط سفرهای فعال می‌توانند توقف کنند."},
                            status=status.HTTP_400_BAD_REQUEST)
        trip.status = Trip.Status.PAUSED
        trip.save()
        return Response(TripDetailSerializer(trip).data)

    @action(detail=True, methods=['patch'])
    def resume(self, request, pk=None):
        trip = self.get_object()
        if trip.driver.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status != Trip.Status.PAUSED:
            return Response({"error": "فقط سفرهای توقف‌شده می‌توانند ادامه یابند."},
                            status=status.HTTP_400_BAD_REQUEST)
        trip.status = Trip.Status.ACTIVE
        trip.save()
        return Response(TripDetailSerializer(trip).data)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        trip = self.get_object()
        if trip.driver.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status in [Trip.Status.COMPLETED, Trip.Status.CANCELLED]:
            return Response({"error": "این سفر قبلاً پایان یافته است."},
                            status=status.HTTP_400_BAD_REQUEST)
        trip.status = Trip.Status.CANCELLED
        trip.end_time = timezone.now()
        trip.save()
        return Response(TripDetailSerializer(trip).data)

    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        trip = self.get_object()
        if trip.driver.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status not in [Trip.Status.ACTIVE, Trip.Status.PAUSED]:
            return Response({"error": "..."}, status=status.HTTP_400_BAD_REQUEST)

        trip.status = Trip.Status.COMPLETED
        trip.end_time = timezone.now()
        trip.save()

        # محاسبه درآمد از سرویس خارجی
        try:
            client = AnalyticsServiceClient()
            start_ts = int(trip.start_time.timestamp())
            end_ts = int(trip.end_time.timestamp())
            result = client.calculate_earnings(
                vehicle_id=trip.vehicle.plate_number,
                start_ts=start_ts,
                end_ts=end_ts
            )
            trip.earnings = result.get("earnings", 0)
            trip.save(update_fields=["earnings"])
            fetch_and_store_trip_analysis.delay(trip.id)

        except Exception as e:
            logger.error(f"Earnings calculation failed for trip {trip.id}: {e}")
            # در صورت خطا، earnings صفر می‌ماند اما سفر کامل شده است

        return Response(TripDetailSerializer(trip).data)

    @action(detail=True, methods=['get'])
    def analysis(self, request, pk=None):
        trip = self.get_object()
        if trip.driver.user_id != request.user.id and not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            analysis = trip.analysis
        except TripAnalysis.DoesNotExist:
            return Response({"detail": "هنوز تحلیلی ثبت نشده است."}, status=404)

        serializer = TripAnalysisSerializer(analysis)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def refresh_analysis(self, request, pk=None):
        trip = self.get_object()
        if trip.driver.user_id != request.user.id and not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # فراخوانی تسک Celery برای به‌روزرسانی
        fetch_and_store_trip_analysis.delay(trip.id)
        return Response({"message": "درخواست به‌روزرسانی تحلیل ثبت شد."}, status=202)

    @action(detail=False, methods=['get'])
    def my_analysis_list(self, request):
        """لیست تحلیل‌های همهٔ سفرهای راننده جاری"""
        analyses = TripAnalysis.objects.filter(trip__driver__user=request.user)
        serializer = TripAnalysisSerializer(analyses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        # فیلتر بر اساس پارامترها
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        driver_id = request.query_params.get('driver_id')
        campaign_id = request.query_params.get('campaign_id')

        trips = Trip.objects.select_related('analysis', 'driver__user', 'campaign', 'vehicle')

        if start_date:
            trips = trips.filter(start_time__date__gte=start_date)
        if end_date:
            trips = trips.filter(end_time__date__lte=end_date)
        if driver_id:
            trips = trips.filter(driver_id=driver_id)
        if campaign_id:
            trips = trips.filter(campaign_id=campaign_id)

        # فقط سفرهای کامل شده
        trips = trips.filter(status=Trip.Status.COMPLETED)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="trip_analysis.csv"'
        writer = csv.writer(response)

        # هدر CSV
        writer.writerow([
            'trip_id', 'driver_phone', 'vehicle_plate', 'campaign_title',
            'start_time', 'end_time',
            'active_seconds', 'distance_km', 'exposure_score',
            'estimated_impressions', 'earnings'
        ])

        for trip in trips:
            analysis = getattr(trip, 'analysis', None)
            writer.writerow([
                trip.id,
                trip.driver.user.phone if trip.driver else '',
                trip.vehicle.plate_number if trip.vehicle else '',
                trip.campaign.slogan if trip.campaign else '',
                trip.start_time,
                trip.end_time,
                analysis.active_seconds if analysis else '',
                analysis.distance_km if analysis else '',
                analysis.exposure_score if analysis else '',
                analysis.estimated_impressions if analysis else '',
                trip.earnings
            ])

        return response

    @action(detail=True, methods=['get'])
    def current_earnings(self, request, pk=None):
        trip = self.get_object()
        if trip.driver.user != request.user and not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if not trip.start_time:
            return Response({"earnings": 0})

        end_ts = int(timezone.now().timestamp())
        start_ts = int(trip.start_time.timestamp())
        client = AnalyticsServiceClient()
        result = client.calculate_earnings(trip.vehicle.plate_number, start_ts, end_ts)
        return Response(result)

    @action(detail=True, methods=['patch'], url_path='upload-installation')
    def upload_installation(self, request, pk=None):
        trip = self.get_object()
        if trip.driver.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = InstallationUploadSerializer(trip, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # اگر هر دو عکس آپلود شده باشند، به‌طور خودکار تأیید اولیه (اختیاری)
        if trip.sticker_image and trip.driver_car_image:
            trip.installation_verified = True
            trip.installation_verified_at = timezone.now()
            trip.save()

        return Response(TripDetailSerializer(trip).data)

class DriverHomeView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDriverUser]

    def get(self, request):
        user = request.user
        driver_profile = user.driver_profile

        # ۱. خلاصه پروفایل
        profile_data = {
            'name': driver_profile.full_name,
            'avatar': driver_profile.avatar.url if driver_profile.avatar else None,
            'wallet_balance': user.wallet.balance,
            'kyc_status': driver_profile.kyc_status,
        }

        # آخرین موقعیت راننده
        last_location = DriverLocation.objects.filter(driver=user).order_by('-timestamp').first()
        if last_location:
            profile_data['last_location'] = {
                'lat': last_location.point.y,
                'lng': last_location.point.x,
                'timestamp': last_location.timestamp.isoformat()
            }

        # ۲. سفر فعال
        active_trip = Trip.objects.filter(
            driver=driver_profile,
            status__in=[Trip.Status.ACTIVE, Trip.Status.PAUSED]
        ).select_related('campaign', 'vehicle', 'campaign__area', 'campaign__design__print_shop').first()

        if active_trip:
            trip_serializer = DriverTripDetailSerializer(active_trip)
            campaign_data = None
            status = 'active_trip'
        else:
            # ۳. کمپین‌های در دسترس
            # فیلتر بر اساس شهر راننده (از پروفایل یا آخرین موقعیت)
            city = driver_profile.city
            available_campaigns = Campaign.objects.filter(
                status=Campaign.Status.ACTIVE,
                start_date__lte=date.today(),
                end_date__gte=date.today()
            )
            if city:
                available_campaigns = available_campaigns.filter(area__city=city)

            campaign_serializer = AvailableCampaignSerializer(available_campaigns, many=True)
            campaign_data = campaign_serializer.data
            trip_serializer = None
            status = 'no_active_trip'

        # ۴. اعلان‌های خوانده‌نشده
        unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()

        return Response({
            'profile': profile_data,
            'status': status,
            'active_trip': trip_serializer.data if trip_serializer else None,
            'available_campaigns': campaign_data,
            'unread_notifications': unread_notifications,
        })

#------------- DRIVER RATING ------------#

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsClientUser])
def rate_driver(request, trip_id):
    try:
        trip = Trip.objects.get(
            id=trip_id,
            campaign__brand_name__client__user=request.user,
            status=Trip.Status.COMPLETED
        )
    except Trip.DoesNotExist:
        return Response({"error": "سفر یافت نشد یا متعلق به شما نیست"}, status=404)

    rating = request.data.get('rating')
    if not rating or int(rating) not in range(1, 6):
        return Response({"error": "امتیاز باید بین ۱ تا ۵ باشد"}, status=400)

    trip.rating = int(rating)
    trip.feedback = request.data.get('feedback', '')
    trip.save()
    return Response({"message": "امتیاز با موفقیت ثبت شد"})