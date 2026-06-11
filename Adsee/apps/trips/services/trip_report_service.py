import csv
from django.http import HttpResponse
from trips.models import Trip


class TripReportService:
    """سرویس گزارش‌گیری سفرها"""

    @staticmethod
    def get_filtered_trips(start_date=None, end_date=None, driver_id=None, campaign_id=None):
        """سفرهای کامل‌شده با امکان فیلتر"""
        trips = Trip.objects.select_related('analysis', 'driver__user', 'campaign', 'vehicle')
        if start_date:
            trips = trips.filter(start_time__date__gte=start_date)
        if end_date:
            trips = trips.filter(end_time__date__lte=end_date)
        if driver_id:
            trips = trips.filter(driver_id=driver_id)
        if campaign_id:
            trips = trips.filter(campaign_id=campaign_id)
        return trips.filter(status=Trip.Status.COMPLETED)

    @staticmethod
    def generate_csv_response(trips, filename='trip_analysis.csv'):
        """تولید HttpResponse حاوی فایل CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

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