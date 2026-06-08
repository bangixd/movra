from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from campaigns.models import Campaign, CampaignSetting
from campaigns.serializers import CampaignSettingSerializer
from campaigns.services.campaign_setting_service import CampaignSettingService
from utils.permissions import IsClientUser, IsOwnerOrAdmin


class CampaignSettingViewSet(ModelViewSet):
    """
    مدیریت تنظیمات کمپین
    """
    permission_classes = [IsAuthenticated, IsClientUser, IsOwnerOrAdmin]
    serializer_class = CampaignSettingSerializer

    def get_queryset(self):
        return CampaignSettingService.get_queryset(self.request.user)

    def perform_create(self, serializer):
        # دریافت campaign_id از داده‌های ارسالی
        campaign_id = self.request.data.get('campaign')
        if not campaign_id:
            raise serializers.ValidationError({"campaign": "شناسهٔ کمپین الزامی است."})

        # بررسی مالکیت کمپین
        campaign = get_object_or_404(
            Campaign,
            id=campaign_id,
            client__user=self.request.user
        )

        # ذخیره تنظیمات
        serializer.save(campaign=campaign)

    def perform_update(self, serializer):
        # در ویرایش، کمپین را از instance فعلی می‌خوانیم
        instance = self.get_object()
        campaign = instance.campaign

        # اگر کمپین در حال تغییر است (در داده‌های ارسالی campaign جدید آمده)
        new_campaign_id = self.request.data.get('campaign')
        if new_campaign_id and str(new_campaign_id) != str(campaign.id):
            campaign = get_object_or_404(
                Campaign,
                id=new_campaign_id,
                client__user=self.request.user
            )

        serializer.save(campaign=campaign)