from rest_framework import serializers
from trips.models import Trip, TripAnalysis


class InstallationUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['sticker_image', 'driver_car_image']