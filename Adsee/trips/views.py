from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Trip
from .serializers import (
    TripCreateSerializer,
    TripListSerializer,
    TripDetailSerializer,
    TripStatusUpdateSerializer,
)
from campaigns.models import Campaign
from campaigns.serializers import CampaignBriefSerializer
from permissions import IsDriverUser

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
            start_date__lte=now.date(),
            end_date__gte=now.date()
        )
        city_id = request.query_params.get('city_id')
        if city_id:
            try:
                city_id = int(city_id)
            except (TypeError, ValueError):
                return Response({"error": "city_id نامعتبر است."},
                                status=status.HTTP_400_BAD_REQUEST)
            campaigns = campaigns.filter(area__city_id=city_id)

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
    def complete(self, request, pk=None):
        trip = self.get_object()
        if trip.driver.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if trip.status not in [Trip.Status.ACTIVE, Trip.Status.PAUSED]:
            return Response({"error": "فقط سفرهای فعال/توقف‌شده می‌توانند پایان یابند."},
                            status=status.HTTP_400_BAD_REQUEST)
        trip.status = Trip.Status.COMPLETED
        trip.end_time = timezone.now()
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