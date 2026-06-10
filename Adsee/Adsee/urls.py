from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,    # برای گرفتن access token جدید با refresh token
    TokenVerifyView,      # برای چک کردن اعتبار access token
    TokenBlacklistView  # برای لاگ اوت کردن
)


schema_view = get_schema_view(
   openapi.Info(
      title="Adsee API", # عنوان API شما
      default_version='v1',
      description="API documentation for Adsee project",
      # terms_of_service="https://www.google.com/policies/terms/",
      # contact=openapi.Contact(email="contact@adsee.local"),
      # license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny,], # یا سطح دسترسی مورد نظر
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/', include('accounts.urls')),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # debug mode only اندپوینت لاگین
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # اندپوینت تمدید توکن
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),  # این URL برای لاگ اوت

    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('v1/drivers/', include('drivers.urls')),
    path('v1/clients/', include('clients.urls')),
    path('v1/campaigns/', include('campaigns.urls')),
    path('v1/geo/', include('geo.urls')),
    path('api/vehicles/', include('vehicles.urls')),
    path('v1/brands/', include('brands.urls')),
    path('api/trips/', include('trips.urls')),
    path('api/print_shops/', include('print_shops.urls')),
    path('v1/notifications/', include('notifications.urls')),
    path('api/wallets/', include('wallets.urls')),
    path('api/support/', include('support.urls')),
    path('v1/blogs/', include('blogs.urls')),


]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)