from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from trips.services.trip_driver_home_service import DriverHomeService
from utils.permissions import IsDriverUser


class DriverHomeView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDriverUser]

    def get(self, request):
        data = DriverHomeService.get_dashboard_data(request.user)
        return Response(data)