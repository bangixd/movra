from rest_framework import viewsets, permissions
from wallets.serializers import BankAccountSerializer
from wallets.services.bank_account_service import BankAccountService


class BankAccountViewSet(viewsets.ModelViewSet):
    """
    مدیریت حساب‌های بانکی.

    ### متدهای اصلی:
    - **GET /wallet/bank/**: لیست حساب‌های بانکی کاربر
    - **POST /wallet/bank/**: افزودن حساب بانکی جدید
      - Body: `{"card_number": "6037...", "sheba_number": "IR...", "bank_name": "ملی"}`
    - **GET /wallet/bank/{id}/**: جزئیات یک حساب
    - **PUT/PATCH /wallet/bank/{id}/**: ویرایش حساب
    - **DELETE /wallet/bank/{id}/**: حذف حساب

    ### محدودیت‌ها:
    - فقط کاربران احراز هویت‌شده
    - هر کاربر فقط حساب‌های خود را می‌بیند و مدیریت می‌کند
    """
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BankAccountService.get_queryset(self.request.user)

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user.driver_profile)