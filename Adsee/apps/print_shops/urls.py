from django.urls import path, include
from .views import AssignedDesignsListView, UpdateDesignPrintStatusView
from .router import router

urlpatterns = router.urls + [
    path('designs/', AssignedDesignsListView.as_view(), name='assigned-designs'),
    path('designs/<int:design_id>/status/', UpdateDesignPrintStatusView.as_view(), name='design-status-update'),

]