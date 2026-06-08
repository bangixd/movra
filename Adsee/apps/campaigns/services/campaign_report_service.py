import csv
from django.http import HttpResponse
from trips.models import TripAnalysis, Trip


class CampaignReportService:
    """سرویس گزارش‌گیری از کمپین"""

    @staticmethod
    def check_access(user, campaign) -> None:
        """
        بررسی دسترسی کاربر به کمپین
        Raises: PermissionError در صورت عدم دسترسی
        """
        if not user.is_staff and campaign.client.user != user:
            raise PermissionError("شما به این کمپین دسترسی ندارید.")

    @staticmethod
    def get_completed_trip_analyses(campaign):
        """
        برگرداندن تحلیل‌های سفرهای کامل‌شدهٔ یک کمپین
        """
        return TripAnalysis.objects.filter(
            trip__campaign=campaign,
            trip__status=Trip.Status.COMPLETED
        ).select_related('trip__driver', 'trip__vehicle', 'trip__campaign')

    @staticmethod
    def generate_csv_response(campaign, analyses) -> HttpResponse:
        """
        تولید فایل CSV از تحلیل‌های سفر
        Args:
            campaign: نمونهٔ کمپین
            analyses: کوئری‌ست از TripAnalysis
        Returns:
            HttpResponse با content-type text/csv
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="campaign_{campaign.id}_analysis.csv"'
        response.write('\ufeff'.encode('utf8'))  # BOM برای نمایش فارسی درست
        writer = csv.writer(response)

        # هدر
        writer.writerow([
            'شناسه سفر', 'نام راننده', 'پلاک خودرو', 'عنوان کمپین',
            'زمان شروع', 'زمان پایان',
            'مدت فعال (ثانیه)', 'مسافت (کیلومتر)', 'امتیاز نمایش',
            'تخمین تعداد مشاهده', 'درآمد (تومان)'
        ])

        for analysis in analyses:
            trip = analysis.trip
            writer.writerow([
                trip.id,
                trip.driver.full_name if trip.driver else '',
                trip.vehicle.plate_number if trip.vehicle else '',
                campaign.slogan,
                trip.start_time.strftime('%Y-%m-%d %H:%M:%S') if trip.start_time else '',
                trip.end_time.strftime('%Y-%m-%d %H:%M:%S') if trip.end_time else '',
                analysis.active_seconds,
                analysis.distance_km,
                analysis.exposure_score,
                analysis.estimated_impressions,
                trip.earnings
            ])

        return response

    @staticmethod
    def get_trip_analyses_for_campaign(campaign_id, user):
        """
        برگرداندن تحلیل‌های سفر یک کمپین با در نظر گرفتن سطح دسترسی
        - ادمین: همهٔ تحلیل‌ها
        - کلاینت: فقط تحلیل‌های کمپین‌های خودش
        """
        if user.is_staff:
            return TripAnalysis.objects.filter(trip__campaign_id=campaign_id)

        return TripAnalysis.objects.filter(
            trip__campaign_id=campaign_id,
            trip__campaign__client__user=user
        )