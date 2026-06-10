from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from notifications.serializers import NotificationSerializer
from notifications.services.notification_service import NotificationService


class NotificationViewSet(viewsets.ModelViewSet):
    """
    مدیریت اعلان‌های کاربر.

    ### متدهای اصلی:
    - **GET /notifications/**: لیست اعلان‌های کاربر جاری (جدیدترین‌ها اول)
    - **GET /notifications/{id}/**: جزئیات یک اعلان
    - **DELETE /notifications/{id}/**: حذف اعلان

    ### اکشن‌های اختصاصی:
    - **POST /notifications/{id}/read/**: علامت‌گذاری یک اعلان به‌عنوان خوانده‌شده
      - Response: `{"status": "read"}`

    - **POST /notifications/read_all/**: علامت‌گذاری همهٔ اعلان‌ها به‌عنوان خوانده‌شده
      - Response: `{"status": "all read", "count": 5}`

    ### محدودیت‌ها:
    - فقط کاربران احراز هویت‌شده دسترسی دارند.
    - هر کاربر فقط اعلان‌های خود را می‌بیند.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationService.get_queryset(self.request.user)

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """علامت‌گذاری یک اعلان به‌عنوان خوانده‌شده"""
        notification = self.get_object()
        NotificationService.mark_as_read(notification)
        return Response({'status': 'read'})

    @action(detail=False, methods=['post'])
    def read_all(self, request):
        """علامت‌گذاری همهٔ اعلان‌ها به‌عنوان خوانده‌شده"""
        count = NotificationService.mark_all_as_read(request.user)
        return Response({'status': 'all read', 'count': count})