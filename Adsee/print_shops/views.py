from rest_framework import viewsets, permissions, generics
from .models import PrintShopProfile
from .serializers import PrintShopProfileSerializer
from campaigns.models import CampaignDesign
from campaigns.serializers import CampaignDesignSerializer
from permissions import IsOwnerOrAdmin, IsPrintShopUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from campaigns.models import CampaignDesign


class PrintShopProfileViewSet(viewsets.ModelViewSet):
    serializer_class = PrintShopProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsPrintShopUser]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return PrintShopProfile.objects.none()
        if user.is_staff:
            return PrintShopProfile.objects.all()
        return PrintShopProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AssignedDesignsListView(generics.ListAPIView):
    serializer_class = CampaignDesignSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # فقط طرح‌هایی که به چاپخانهٔ فعلی ارجاع شده‌اند
        return CampaignDesign.objects.filter(print_shop__user=self.request.user)


class UpdateDesignPrintStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, design_id):
        try:
            design = CampaignDesign.objects.get(
                id=design_id,
                print_shop__user=request.user  # فقط چاپخانهٔ صاحب طرح
            )
        except CampaignDesign.DoesNotExist:
            return Response({"error": "Not found or not yours"}, status=404)

        new_status = request.data.get('print_status')
        estimated = request.data.get('estimated_ready_date')
        if new_status:
            design.print_status = new_status
        if estimated:
            design.estimated_ready_date = estimated
        design.save()
        return Response(CampaignDesignSerializer(design).data)