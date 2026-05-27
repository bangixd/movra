from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
import csv
from django.utils import timezone
from .models import Trip, TripAnalysis
from .serializers import (
    TripCreateSerializer,
    TripListSerializer,
    TripDetailSerializer,
    TripStatusUpdateSerializer,
    TripAnalysisSerializer,
)
from campaigns.models import Campaign
from campaigns.serializers import CampaignBriefSerializer
from permissions import IsDriverUser
from services.tasks import update_earnings_task, fetch_and_store_trip_analysis
from services.analytics_client import AnalyticsServiceClient
import logging
logger = logging.getLogger(__name__)

class TripViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsDriverUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return TripCreateSerializer
        elif self.action in ['start', 'pause', 'resume', 'complete', 'cancel']:
            return TripStatusUpdateSerializer
        elif self.action == 'list':
            return TripListSerializer
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