from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientProfileViewSet, ClientDocumentViewSet

router = DefaultRouter()
router.register(r'documents', ClientDocumentViewSet, basename='client-document')
router.register(r'', ClientProfileViewSet, basename='client-profile')
urlpatterns = router.urls