from django.contrib.gis.geos import Point
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from clients.models import ClientProfile

User = get_user_model()


class ClientProfileService:
    """Service for managing client profiles"""

    @staticmethod
    def get_queryset(user):
        """Return profiles based on user role."""
        if not user.is_authenticated:
            return ClientProfile.objects.none()
        if user.is_staff:
            return ClientProfile.objects.all()
        return ClientProfile.objects.filter(user=user)

    @staticmethod
    def get_or_create_profile(user) -> ClientProfile:
        """Get existing profile or create a new one for the user."""
        profile, _ = ClientProfile.objects.get_or_create(
            user=user,
            defaults={'advertiser_type': ClientProfile.AdvertiserType.REAL}
        )
        return profile

    @staticmethod
    def set_location(profile, lat: float, lng: float) -> dict:
        """Update the client's location."""
        point = Point(lng, lat, srid=4326)
        profile.location = point
        profile.save(update_fields=['location'])
        return {
            "message": "موقعیت مکانی با موفقیت ذخیره شد",
            "location": {"lat": lat, "lng": lng}
        }

    @staticmethod
    def select_advertiser_type(profile, adv_type: str) -> dict:
        """Set the advertiser type and advance KYC step."""
        valid_types = [ClientProfile.AdvertiserType.REAL, ClientProfile.AdvertiserType.LEGAL]
        if adv_type not in valid_types:
            raise ValueError("نوع فعالیت نامعتبر است")

        profile.advertiser_type = adv_type
        profile.kyc_step = ClientProfile.KYCStep.UPLOAD_DOCUMENTS
        profile.save(update_fields=['advertiser_type', 'kyc_step'])

        return {
            "message": "نوع فعالیت با موفقیت ثبت شد",
            "kyc_step": profile.kyc_step
        }