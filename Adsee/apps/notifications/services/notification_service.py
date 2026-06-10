from notifications.models import Notification


class NotificationService:
    """سرویس مدیریت اعلان‌ها"""

    @staticmethod
    def get_queryset(user):
        """
        برگرداندن اعلان‌های کاربر جاری.
        """
        if not user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(recipient=user)

    @staticmethod
    def mark_as_read(notification: Notification) -> Notification:
        """
        علامت‌گذاری یک اعلان به‌عنوان خوانده‌شده.
        """
        notification.is_read = True
        notification.save()
        return notification

    @staticmethod
    def mark_all_as_read(user):
        """
        علامت‌گذاری همهٔ اعلان‌های کاربر به‌عنوان خوانده‌شده.
        Returns: تعداد اعلان‌های به‌روزرسانی‌شده
        """
        count = Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
        return count