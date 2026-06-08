from rest_framework import serializers
from campaigns.models import CampaignSetting

class CampaignSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignSetting
        fields = [
            'id',
            'campaign',
            'active_days',
            'activity_hours_per_day',
            'max_driver',
            'vehicle_type',
        ]
        read_only_fields = ['id', 'campaign']

    def validate(self, attrs):
        """
        اعتبارسنجی‌های سفارشی برای داده‌های ورودی.
        """
        activity_hours_per_day = attrs.get('activity_hours_per_day', getattr(self.instance, 'activity_hours_per_day', None))
        vehicle_type = attrs.get('vehicle_type', getattr(self.instance, 'vehicle_type', None))

        # اعتبارسنجی ۱: اطمینان از اینکه activity_hours_per_day منطقی است
        # اگر محدودیت خاصی مثلاً بیشتر از ۱۲ ساعت در روز نباشد، اینجا اضافه می‌شود.
        if activity_hours_per_day and (activity_hours_per_day.hour > 12 or (activity_hours_per_day.hour == 12 and activity_hours_per_day.minute > 0)):
             raise serializers.ValidationError({
                 "activity_hours_per_day": "ساعات فعالیت روزانه نباید بیشتر از ۱۲ ساعت باشد."
             })

        if not vehicle_type:
            raise serializers.ValidationError({
                "vehicle_type": "نوع خودرو الزامی است."
            })

        return attrs

    def create(self, validated_data):
        """
        وقتی داده‌ها اعتبارسنجی شدند، یک نمونه جدید ایجاد می‌کند.
        """
        return CampaignSetting.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        وقتی داده‌ها اعتبارسنجی شدند، نمونه موجود را به‌روزرسانی می‌کند.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
