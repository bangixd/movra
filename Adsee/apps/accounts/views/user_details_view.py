from django.contrib.auth import get_user_model
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.serializers import (UserSerializer, )
from utils.permissions import IsOwnerOrAdmin

User = get_user_model()

class UserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    throttle_classes = [UserRateThrottle]
    throttle_scope = 'user'

    def get(self, request):
        user = request.user  # کاربر جاری که نیاز داریم اطلاعاتش رو برگردونیم
        serializer = UserSerializer(user)
        return Response(serializer.data)