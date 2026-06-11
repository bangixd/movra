from rest_framework import serializers
from trips.models import Trip, TripAnalysis
from datetime import date


class DriverTripListSerializer(serializers.ModelSerializer):
    """برای لیست سفرها (خلاصه)"""
    brand_name = serializers.CharField(source='campaign.brand_name.name', read_only=True)
    area_name = serializers.CharField(source='campaign.area.area_type', read_only=True)  # یا نام شهر
    remaining_hours = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id', 'brand_name', 'area_name', 'status',
            'remaining_hours', 'remaining_days',
            'start_time', 'end_time',
            'earnings', 'total_distance_km'
        ]

    def get_remaining_days(self, obj):
        campaign = obj.campaign
        if campaign and campaign.end_date:
            today = date.today()
            if campaign.end_date >= today:
                return (campaign.end_date - today).days
        return 0

    def get_remaining_hours(self, obj):
        """بر اساس روزهای باقی‌مانده و ساعت فعالیت روزانه کمپین"""
        remaining_days = self.get_remaining_days(obj)
        if remaining_days > 0:
            try:
                setting = obj.campaign.setting
                hours_per_day = setting.activity_hours_per_day.hour if setting.activity_hours_per_day else 8
                return remaining_days * hours_per_day
            except:
                pass
        return 0


class DriverTripDetailSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='campaign.brand_name.name', read_only=True)
    area_name = serializers.CharField(source='campaign.area.area_type', read_only=True)
    city_name = serializers.CharField(source='campaign.area.city.name', read_only=True, allow_null=True)
    remaining_hours = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()
    distance_km = serializers.FloatField(source='analysis.distance_km', read_only=True, default=0.0)
    current_earnings = serializers.SerializerMethodField()
    deductions = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    print_shop_address = serializers.CharField(source='campaign.design.print_shop.address', read_only=True, allow_null=True)
    area_geometry = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id', 'brand_name', 'area_name', 'city_name', 'status',
            'start_time', 'end_time',
            'remaining_hours', 'remaining_days',
            'distance_km', 'current_earnings',
            'deductions', 'paid_amount',
            'earnings', 'total_distance_km',
            'campaign', 'vehicle',
            'sticker_image', 'driver_car_image', 'installation_verified',
            'print_shop_address', 'area_geometry'
        ]


    def get_remaining_days(self, obj):
        campaign = obj.campaign
        if campaign and campaign.end_date:
            today = date.today()
            if campaign.end_date >= today:
                return (campaign.end_date - today).days
        return 0

    def get_remaining_hours(self, obj):
        """بر اساس روزهای باقی‌مانده و ساعت فعالیت روزانه کمپین"""
        remaining_days = self.get_remaining_days(obj)
        if remaining_days > 0:
            try:
                setting = obj.campaign.setting
                hours_per_day = setting.activity_hours_per_day.hour if setting.activity_hours_per_day else 8
                return remaining_days * hours_per_day
            except:
                pass
        return 0

    def get_current_earnings(self, obj):
        """درآمد تا این لحظه (برای سفرهای فعال از API خارجی گرفته می‌شود)"""
        if obj.status == Trip.Status.ACTIVE and obj.start_time:
            # اینجا می‌توانیم از سرویس analytics بگیریم، اما برای سادگی از فیلد earnings صرف نظر می‌کنیم
            # یا یک تسک Celery برای به‌روزرسانی دوره‌ای earnings دارد.
            return obj.earnings  # موقتاً همان earnings نهایی که ممکن است هنوز محاسبه نشده باشد
        return obj.earnings

    def get_deductions(self, obj):
        if hasattr(obj, 'analysis') and obj.analysis:
            raw = obj.analysis.raw_response
            return {
                'night_factor': raw.get('night_income_factor', 1.0),
                'long_stop_factor': raw.get('long_stop_income_factor', 1.0),
                'suspicious_stop_penalty': raw.get('suspicious_stop_penalty_factor', 0.0),
                'invalid_data_penalty': raw.get('invalid_data_penalty_factor', 0.0),
                'total_penalty_amount': raw.get('total_penalty_amount', 0),
            }
        return {}
    def get_paid_amount(self, obj):
        """مبلغ پرداخت‌شده به راننده (آخرین تراکنش موفق)"""
        if obj.status == Trip.Status.COMPLETED:
            tx = obj.wallet_transactions.filter(
                transaction_type='INCOME',
                status='SUCCESS'
            ).first()
            if tx:
                return tx.amount
        return None

    def get_area_geometry(self, obj):
        if hasattr(obj.campaign, 'area') and obj.campaign.area:
            geom = obj.campaign.area.get_targeting_area_geometry()
            if geom:
                return geom.json
        return None
