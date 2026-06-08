from rest_framework import serializers

class CampaignCostCalculationSerializer(serializers.Serializer):
    drivers_count = serializers.IntegerField(min_value=1)
    days_count = serializers.IntegerField(min_value=1)
    hours_per_day = serializers.IntegerField(min_value=1)
    vehicle_type_id = serializers.IntegerField()
    design_type = serializers.ChoiceField(choices=["READY_TEMPLATE", "UPLOADED_DESIGN", "CUSTOM_DESIGN"])
    area_type = serializers.ChoiceField(choices=["FREE", "SUGGESTED_ROUTE", "CIRCLE"])
