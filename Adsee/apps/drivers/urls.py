from django.urls import path, include
from .views import apply_referral_code
from .router import router

urlpatterns =  [
    path('apply-referral/', apply_referral_code, name='apply-referral'),
] + router.urls