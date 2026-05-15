from django.contrib.gis.geos import Point
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models import Trip
from .serializers import (
    TripCreateSerializer,
    TripListSerializer,
    TripDetailSerializer,
    TripStatusUpdateSerializer,
)
from ..campaigns.models import Campaign
from ..campaigns.serializers import CampaignBriefSerializer
from ..core.permissions import IsDriverUser


class TripViewSet(viewsets.ModelViewSet):
    permission_classes = [IsDriverUser]
    queryset = Trip.objects.all()

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
        if user.is_staff:
            return Trip.objects.all()
        return Trip.objects.filter(driver=user)

    @action(detail=False, methods=['get'])
    def available_campaigns(self, request):
        """
        کمپین‌هایی که راننده می‌تواند انتخاب کند.
        """
        now = timezone.now()
        campaigns = Campaign.objects.filter(
            status='PUBLISHED',
            start_date__lte=now,
            end_date__gte=now
        )
        # می‌توان فیلتر موقعیت مکانی هم گذاشت
        # مثلاً کمپین‌هایی که شهرشان با موقعیت فعلی راننده یکیست
        # فعلاً ساده همه را برمی‌گردانیم
        serializer = CampaignBriefSerializer(campaigns, many=True)  # یک سریالایزر خلاصه از کمپین
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        سفر فعال راننده (PENDING / ACTIVE / PAUSED)
        """
        trip = Trip.objects.filter(
            driver=request.user
        ).exclude(
            status__in=[Trip.Status.COMPLETED, Trip.Status.CANCELLED]
        ).first()
        if trip:
            serializer = TripDetailSerializer(trip)
            return Response(serializer.data)
        return Response({"detail": "سفر فعالی ندارید."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['patch'])
    def start(self, request, pk=None):
        trip = self.get_object()
        if trip.driver != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status != Trip.Status.PENDING:
            return Response({"error": "فقط سفرهای در انتظار می‌توانند شروع شوند."}, status=status.HTTP_400_BAD_REQUEST)
        trip.status = Trip.Status.ACTIVE
        trip.start_time = timezone.now()
        trip.save()
        return Response(TripDetailSerializer(trip).data)

    @action(detail=True, methods=['patch'])
    def pause(self, request, pk=None):
        trip = self.get_object()
        if trip.driver != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status != Trip.Status.ACTIVE:
            return Response({"error": "فقط سفرهای فعال می‌توانند توقف کنند."}, status=status.HTTP_400_BAD_REQUEST)
        trip.status = Trip.Status.PAUSED
        trip.save()
        return Response(TripDetailSerializer(trip).data)

    @action(detail=True, methods=['patch'])
    def resume(self, request, pk=None):
        trip = self.get_object()
        if trip.driver != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status != Trip.Status.PAUSED:
            return Response({"error": "فقط سفرهای توقف‌شده می‌توانند ادامه یابند."}, status=status.HTTP_400_BAD_REQUEST)
        trip.status = Trip.Status.ACTIVE
        trip.save()
        return Response(TripDetailSerializer(trip).data)

    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        trip = self.get_object()
        if trip.driver != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status not in [Trip.Status.ACTIVE, Trip.Status.PAUSED]:
            return Response({"error": "فقط سفرهای فعال/توقف‌شده می‌توانند پایان یابند."}, status=status.HTTP_400_BAD_REQUEST)
        trip.status = Trip.Status.COMPLETED
        trip.end_time = timezone.now()
        # محاسبه درآمد اینجا انجام نمی‌شود (API خارجی)
        trip.save()
        return Response(TripDetailSerializer(trip).data)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        trip = self.get_object()
        if trip.driver != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status in [Trip.Status.COMPLETED, Trip.Status.CANCELLED]:
            return Response({"error": "این سفر قبلاً پایان یافته است."}, status=status.HTTP_400_BAD_REQUEST)
        trip.status = Trip.Status.CANCELLED
        trip.end_time = timezone.now()
        trip.save()
        return Response(TripDetailSerializer(trip).data)

    @action(detail=False, methods=['get'])
    def available_campaigns(self, request):
        """
        کمپین‌های قابل انتخاب برای راننده.
        پارامتر Query اختیاری: city_id
        اگر ارسال شود، فقط کمپین‌های همان شهر برگردانده می‌شوند.
        """
        now = timezone.now()
        campaigns = Campaign.objects.filter(
            status='PUBLISHED',
            start_date__lte=now,
            end_date__gte=now
        )

        city_id = request.query_params.get('city_id')
        if city_id:
            try:
                city_id = int(city_id)
            except (TypeError, ValueError):
                return Response(
                    {"error": "city_id نامعتبر است."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            campaigns = campaigns.filter(area__city_id=city_id)

        serializer = CampaignBriefSerializer(campaigns, many=True)
        return Response(serializer.data)


    # به جهت دریافت لیست کمپین هایی که راننده در محدوده اونها هست
    # @action(detail=False, methods=['get'])
    # def available_campaigns(self, request):
    #     """
    #     لیست کمپین‌های قابل انتخاب برای راننده.
    #     پارامترهای اختیاری Query:
    #     - lat: عرض جغرافیایی راننده
    #     - lng: طول جغرافیایی راننده
    #     """
    #     now = timezone.now()
    #     campaigns = Campaign.objects.filter(
    #         status='PUBLISHED',
    #         start_date__lte=now,
    #         end_date__gte=now
    #     )
    #
    #     lat = request.query_params.get('lat')
    #     lng = request.query_params.get('lng')
    #
    #     if lat is not None and lng is not None:
    #         try:
    #             lat, lng = float(lat), float(lng)
    #             driver_point = Point(lng, lat, srid=4326)  # lon, lat
    #         except (TypeError, ValueError):
    #             return Response(
    #                 {"error": "مختصات نامعتبر است."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #
    #         # فیلتر کمپین‌هایی که نقطهٔ راننده در محدودهٔ آن‌هاست
    #         valid_ids = []
    #         for campaign in campaigns:
    #             try:
    #                 area = campaign.area  # OneToOne به CampaignArea
    #                 geom = area.get_targeting_area_geometry()
    #                 if geom and driver_point.within(geom):
    #                     valid_ids.append(campaign.id)
    #             except Campaign.area.RelatedObjectDoesNotExist:
    #                 pass
    #         campaigns = campaigns.filter(id__in=valid_ids)
    #
    #     serializer = CampaignBriefSerializer(campaigns, many=True)
    #     return Response(serializer.data)