from rest_framework import generics, permissions, status
from campaigns.serializers import CampaignDesignSerializer
from print_shops.services import PrintShopDesignService
from rest_framework.views import APIView
from rest_framework.response import Response
from campaigns.models import CampaignDesign
from utils.permissions import IsPrintShopUser

class AssignedDesignsListView(generics.ListAPIView):
    """
    لیست طرح‌های ارجاع‌شده به چاپخانهٔ فعلی.

    ### GET /printshop/designs/
    فقط کاربران احراز هویت‌شده می‌توانند طرح‌های ارجاع‌شده به چاپخانهٔ خود را ببینند.

    ### نمونه پاسخ:
    ```json
    [
        {
            "id": 1,
            "campaign": 5,
            "design_type": "USER_UPLOAD",
            "status": "PENDING",
            "print_status": "PENDING",
            "estimated_ready_date": null
        },
        ...
    ]
    """
    serializer_class = CampaignDesignSerializer
    permission_classes = [permissions.IsAuthenticated, IsPrintShopUser]

    def get_queryset(self):
        return PrintShopDesignService.get_assigned_designs(self.request.user)


class UpdateDesignPrintStatusView(APIView):
    """
    به‌روزرسانی وضعیت چاپ یک طرح.

    ### PATCH /printshop/designs/{design_id}/status/
    فقط چاپخانهٔ صاحب طرح می‌تواند وضعیت را تغییر دهد.

    """
    permission_classes = [permissions.IsAuthenticated, IsPrintShopUser]

    def patch(self, request, design_id):
        try:
            design = PrintShopDesignService.get_design_for_printshop(design_id, request.user)

        except CampaignDesign.DoesNotExist:
            return Response({"error": "طرح یافت نشد یا متعلق به شما نیست"}, status=status.HTTP_404_NOT_FOUND)

        print_status = request.data.get('print_status')
        estimated = request.data.get('estimated_ready_date')

        updated_design = PrintShopDesignService.update_print_status(design, print_status, estimated)
        serializer = CampaignDesignSerializer(updated_design)
        return Response(serializer.data)