from support.models import Ticket


class SupportTicketService:
    """سرویس مدیریت تیکت‌های پشتیبانی"""

    @staticmethod
    def create_ticket(user=None, validated_data: dict = None) -> Ticket:
        """ایجاد تیکت جدید"""
        if user and user.is_authenticated:
            validated_data['user'] = user
        return Ticket.objects.create(**validated_data)

    @staticmethod
    def get_user_tickets(user):
        """برگرداندن تیکت‌های کاربر جاری"""
        if not user.is_authenticated:
            return Ticket.objects.none()
        return Ticket.objects.filter(user=user).select_related('user').order_by('-created_at')