from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from clients.services.client_home_service import ClientHomeService
from utils.permissions import IsClientUser


class ClientHomeView(APIView):
    """
    صفحهٔ اصلی (داشبورد) کلاینت.

    ### GET /clients/home/
    برگرداندن اطلاعات خلاصه برای نمایش در داشبورد:
    - **profile**: نام، شهر، موقعیت مکانی
    - **packages**: لیست پکیج‌های فعال
    - **my_campaigns**: آخرین کمپین برای هر وضعیت (ACTIVE, COMPLETED, CANCELLED)
    - **unread_notifications**: تعداد اعلان‌های خوانده‌نشده

    ### نمونه پاسخ:
    ```json
    {
        "profile": {"name": "شرکت تست", "city": "تهران", "location": {...}},
        "packages": [...],
        "my_campaigns": {
            "ACTIVE": {"id": 1, "slogan": "...", ...},
            "COMPLETED": null,
            "CANCELLED": null
        },
        "unread_notifications": 3
    }
    """
    permission_classes = [IsAuthenticated, IsClientUser]

    def get(self, request):
        data = ClientHomeService.get_home_data(request.user)
        return Response(data)