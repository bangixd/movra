from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from clients.services import ClientReportService
from utils.permissions import IsClientUser

class ClientReportSummaryView(APIView):
    """
    گزارش خلاصهٔ عملکرد کلاینت.

    ### GET /clients/reports/summary/
    پارامترهای اختیاری Query:
    - `start_date`: فیلتر کمپین‌ها از این تاریخ (YYYY-MM-DD)
    - `end_date`: فیلتر کمپین‌ها تا این تاریخ (YYYY-MM-DD)

    ### نمونه پاسخ:
    ```json
    {
        "total_campaigns": 5,
        "total_hours_seen": 120.5,
        "total_cost": 15000000,
        "total_days": 25
    }
"""
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request):
        client = request.user.client_profile
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        data = ClientReportService.get_summary(client, start_date, end_date)
        return Response(data)

class ClientPeakHoursView(APIView):
    """
    گزارش ساعات اوج فعالیت (توزیع ساعتی).

    ### GET /clients/reports/peak-hours/
    پارامترهای اختیاری Query:
    - `start_date`, `end_date`

    ### نمونه پاسخ:
    ```json
    {
        "chart_data": [
            {"hour": 0, "seconds": 0.0},
            {"hour": 1, "seconds": 0.0},
            ...
            {"hour": 8, "seconds": 4500.5},
            {"hour": 9, "seconds": 7200.0},
            ...
            {"hour": 23, "seconds": 0.0}
        ]
    }
"""
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request):
        client = request.user.client_profile
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        chart_data = ClientReportService.get_peak_hours(client, start_date, end_date)
        return Response({'chart_data': chart_data})

class BillboardComparisonView(APIView):
    """
    مقایسهٔ تأثیر تبلیغات با بیلبورد سنتی.

    ### GET /clients/reports/billboard-comparison/
    پارامترهای اختیاری Query:
    - `start_date`, `end_date`

    ### نمونه پاسخ:
    ```json
    {
        "our_total_impressions": 150000,
        "billboard_daily_impressions": 50000,
        "ratio": 3.0,
        "message": "تأثیر تبلیغات شما معادل ۳ روز نمایش بیلبورد است."
    }
"""
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request):
        client = request.user.client_profile
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        data = ClientReportService.get_billboard_comparison(client, start_date, end_date)
        return Response(data)