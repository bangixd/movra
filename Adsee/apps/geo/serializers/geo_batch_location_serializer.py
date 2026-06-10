from rest_framework import serializers

class BatchLocationSerializer(serializers.Serializer):
    trip_id = serializers.IntegerField(required=True)
    points = serializers.ListField(
        child=serializers.DictField(
            child=serializers.FloatField(),
            allow_empty=False
        ),
        allow_empty=False,
        help_text="لیست نقاط به فرمت [{'lat':..., 'lon':..., 'timestamp':..., 'speed':..., 'heading':...}, ...]"
    )