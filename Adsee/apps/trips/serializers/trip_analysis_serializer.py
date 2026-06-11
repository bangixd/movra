from rest_framework import serializers
from trips.models import Trip, TripAnalysis


class TripAnalysisSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='trip.driver.full_name', read_only=True)
    vehicle_plate = serializers.CharField(source='trip.vehicle.plate_number', read_only=True)
    campaign_title = serializers.CharField(source='trip.campaign.slogan', read_only=True)

    class Meta:
        model = TripAnalysis
        fields = '__all__'