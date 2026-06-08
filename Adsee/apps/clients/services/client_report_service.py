from campaigns.models import Campaign, CampaignInvoice, CampaignPricingRule
from django.db.models import Sum
from trips.models import Trip, TripAnalysis, HourlyActivity


class ClientReportService:
    """سرویس گزارش‌گیری کلاینت"""

    @staticmethod
    def get_summary(client, start_date=None, end_date=None) -> dict:
        """
        خلاصهٔ گزارش کلاینت: تعداد کمپین‌ها، ساعات فعال، هزینهٔ کل، روزهای فعال
        """
        # کمپین‌های این کلاینت
        campaigns = Campaign.objects.filter(client=client)

        if start_date:
            campaigns = campaigns.filter(start_date__gte=start_date)
        if end_date:
            campaigns = campaigns.filter(end_date__lte=end_date)

        # تعداد کمپین‌ها
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

        return {
            'total_campaigns': total_campaigns,
            'total_hours_seen': total_hours,
            'total_cost': float(total_cost),
            'total_days': total_days,
        }

    @staticmethod
    def get_peak_hours(client, start_date=None, end_date=None) -> list:
        """
        Calculate hourly activity distribution for the client's campaigns.
        Uses HourlyActivity if available, otherwise falls back to TripAnalysis.

        Returns:
            list[dict]: [{'hour': 0, 'seconds': 123.4}, ...]
        """
        # Filter campaigns belonging to this client
        campaigns = Campaign.objects.filter(client=client)
        if start_date:
            campaigns = campaigns.filter(start_date__gte=start_date)
        if end_date:
            campaigns = campaigns.filter(end_date__lte=end_date)

        # Get completed trips for these campaigns
        trips = Trip.objects.filter(
            campaign__in=campaigns,
            status=Trip.Status.COMPLETED
        )

        hourly_activity = [0.0] * 24

        # Check if HourlyActivity data exists
        has_hourly_data = HourlyActivity.objects.filter(trip__in=trips).exists()

        if has_hourly_data:
            # Aggregate from HourlyActivity
            aggregates = HourlyActivity.objects.filter(
                trip__in=trips
            ).values('hour').annotate(
                total_seconds=Sum('active_seconds')
            )
            for agg in aggregates:
                hourly_activity[agg['hour']] = agg['total_seconds']
        else:
            # Fallback: approximate using TripAnalysis
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

        return chart_data

    @staticmethod
    def get_billboard_comparison(client, start_date=None, end_date=None) -> dict:
        """
        مقایسهٔ تأثیر تبلیغات با بیلبورد سنتی

        Returns:
            dict: {
                'our_total_impressions': ...,
                'billboard_daily_impressions': ...,
                'ratio': ...,
                'message': ...
            }
        """
        # کمپین‌های این کلاینت
        campaigns = Campaign.objects.filter(client=client)
        if start_date:
            campaigns = campaigns.filter(start_date__gte=start_date)
        if end_date:
            campaigns = campaigns.filter(end_date__lte=end_date)

        # مجموع تخمین نمایش‌ها
        total_impressions = TripAnalysis.objects.filter(
            trip__campaign__in=campaigns,
            trip__status=Trip.Status.COMPLETED
        ).aggregate(total=Sum('estimated_impressions'))['total'] or 0

        # خواندن عدد مبنا از قوانین
        rule = CampaignPricingRule.objects.filter(
            key='BILLBOARD_DAILY_IMPRESSIONS',
            is_active=True
        ).first()
        billboard_impressions = rule.value if rule else 50000

        # محاسبهٔ نسبت
        ratio = round(total_impressions / billboard_impressions, 2) if billboard_impressions > 0 else 0

        return {
            'our_total_impressions': total_impressions,
            'billboard_daily_impressions': billboard_impressions,
            'ratio': ratio,
            'message': f'تأثیر تبلیغات شما معادل {ratio} روز نمایش بیلبورد است.'
        }