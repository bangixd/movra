from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import WalletViewSet, BankAccountViewSet, WithdrawalRequestView, DepositView

router = DefaultRouter()
router.register(r'', WalletViewSet, basename='wallet')
router.register(r'bank', BankAccountViewSet, basename='bank-account')
urlpatterns =  [
    path('withdraw/', WithdrawalRequestView.as_view(), name='withdraw'),
    path('deposit/', DepositView.as_view(), name='deposit'),

] + router.urls
