from rest_framework.routers import DefaultRouter
from .views import SupportContentViewSet

router = DefaultRouter()
router.register(r'content', SupportContentViewSet, basename='support-content')
urlpatterns = router.urls