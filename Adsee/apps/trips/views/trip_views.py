from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from campaigns.serializers import CampaignBriefSerializer
from trips.models import Trip, TripAnalysis
from trips.serializers import (
    TripCreateSerializer,
    TripListSerializer,
    TripDetailSerializer,
    TripStatusUpdateSerializer,
    TripAnalysisSerializer,
    DriverTripListSerializer,
    DriverTripDetailSerializer,
    InstallationUploadSerializer,
)
from trips.services.trip_service import TripService
from trips.services.trip_report_service import TripReportService
from utils.permissions import IsDriverUser


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
        if self.action in ['start', 'pause', 'resume', 'complete', 'cancel']:
            return TripStatusUpdateSerializer
        if self.action == 'list':
            return DriverTripListSerializer
        if self.action == 'retrieve':
            return DriverTripDetailSerializer
        return TripDetailSerializer

    def get_queryset(self):
        return TripService.get_queryset(self.request.user)

    # ----- کمپین‌های در دسترس -----
    @action(detail=False, methods=['get'], url_path='available-campaigns')
    def available_campaigns(self, request):
        city_id = request.query_params.get('city_id')
        if city_id:
            try:
                city_id = int(city_id)
            except (TypeError, ValueError):
                return Response({"error": "city_id نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)
        campaigns = TripService.get_available_campaigns(city_id)
        serializer = CampaignBriefSerializer(campaigns, many=True)
        return Response(serializer.data)

    # ----- سفر فعال -----
    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        trip = TripService.get_active_trip(request.user)
        if trip:
            return Response(TripDetailSerializer(trip).data)
        return Response({"detail": "سفر فعالی ندارید."}, status=status.HTTP_404_NOT_FOUND)

    # ----- شروع سفر -----
    @action(detail=True, methods=['patch'])
    def start(self, request, pk=None):
        try:
            trip = TripService.start_trip(self.get_object(), request.user)
            return Response(TripDetailSerializer(trip).data)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ----- توقف سفر -----
    @action(detail=True, methods=['patch'])
    def pause(self, request, pk=None):
        try:
            trip = TripService.pause_trip(self.get_object(), request.user)
            return Response(TripDetailSerializer(trip).data)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ----- ادامهٔ سفر -----
    @action(detail=True, methods=['patch'])
    def resume(self, request, pk=None):
        try:
            trip = TripService.resume_trip(self.get_object(), request.user)
            return Response(TripDetailSerializer(trip).data)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ----- لغو سفر -----
    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        try:
            trip = TripService.cancel_trip(self.get_object(), request.user)
            return Response(TripDetailSerializer(trip).data)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ----- پایان سفر -----
    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        try:
            trip = TripService.complete_trip(self.get_object(), request.user)
            return Response(TripDetailSerializer(trip).data)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ----- تحلیل سفر -----
    @action(detail=True, methods=['get'])
    def analysis(self, request, pk=None):
        try:
            analysis = TripService.get_trip_analysis(self.get_object(), request.user)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if analysis is None:
            return Response({"detail": "هنوز تحلیلی ثبت نشده است."}, status=404)
        serializer = TripAnalysisSerializer(analysis)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def refresh_analysis(self, request, pk=None):
        try:
            TripService.refresh_analysis(self.get_object(), request.user)
            return Response({"message": "درخواست به‌روزرسانی تحلیل ثبت شد."}, status=202)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)

    # ----- لیست تحلیل‌های راننده -----
    @action(detail=False, methods=['get'])
    def my_analysis_list(self, request):
        analyses = TripAnalysis.objects.filter(trip__driver__user=request.user)
        serializer = TripAnalysisSerializer(analyses, many=True)
        return Response(serializer.data)

    # ----- خروجی CSV -----
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        driver_id = request.query_params.get('driver_id')
        campaign_id = request.query_params.get('campaign_id')

        trips = TripReportService.get_filtered_trips(start_date, end_date, driver_id, campaign_id)
        response = TripReportService.generate_csv_response(trips)
        return response

    # ----- درآمد جاری -----
    @action(detail=True, methods=['get'])
    def current_earnings(self, request, pk=None):
        try:
            result = TripService.get_current_earnings(self.get_object(), request.user)
            return Response(result)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)

    # ----- آپلود عکس نصب -----
    @action(detail=True, methods=['patch'], url_path='upload-installation')
    def upload_installation(self, request, pk=None):
        try:
            trip = TripService.upload_installation(self.get_object(), request.user, request.data)
            return Response(TripDetailSerializer(trip).data)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)