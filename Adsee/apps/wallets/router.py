from rest_framework.routers import DefaultRouter
from .views import WalletViewSet, BankAccountViewSet

router = DefaultRouter()
router.register(r'', WalletViewSet, basename='wallet')
router.register(r'bank', BankAccountViewSet, basename='bank-account')