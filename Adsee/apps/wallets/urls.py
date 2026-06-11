from django.urls import path
from .views import WithdrawalRequestView, DepositView

from .router import router
urlpatterns = [
    path('withdraw/', WithdrawalRequestView.as_view(), name='withdraw'),
    path('deposit/', DepositView.as_view(), name='deposit'),

] + router.urls
