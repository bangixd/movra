from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework import permissions
from support.serializers import TicketCreateSerializer, TicketListSerializer
from support.services.support_ticket_service import SupportTicketService


class TicketCreateView(CreateAPIView):
    """
    ایجاد تیکت پشتیبانی جدید.

    POST /support/tickets/

    - کاربران لاگین‌شده: تیکت به حسابشان متصل می‌شود
    - کاربران مهمان: تیکت بدون اتصال به حساب ایجاد می‌شود
    """
    serializer_class = TicketCreateSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        SupportTicketService.create_ticket(
            user=self.request.user,
            validated_data=serializer.validated_data
        )


class TicketListView(ListAPIView):
    """
    لیست تیکت‌های کاربر جاری.

    GET /support/tickets/mine/
    """
    serializer_class = TicketListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SupportTicketService.get_user_tickets(self.request.user)