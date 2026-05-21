from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientProfileViewSet, ClientDocumentViewSet

router = DefaultRouter()
router.register(r'profile', ClientProfileViewSet, basename='client-profile')
router.register(r'documents', ClientDocumentViewSet, basename='client-document')
urlpatterns = router.urls