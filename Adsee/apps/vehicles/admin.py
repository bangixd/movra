from django.contrib import admin
from .models import VehicleType, Vehicle


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_hourly_rate', 'is_active', 'updated_at']
    list_editable = ['base_hourly_rate', 'is_active']      # ویرایش مستقیم نرخ
    search_fields = ['name']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'driver', 'vehicle_type', 'hourly_rate', 'is_active']
    list_filter = ['vehicle_type', 'is_active']
    search_fields = ['plate_number', 'driver__email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('مالک', {'fields': ('driver',)}),
        ('نوع خودرو', {'fields': ('vehicle_type',)}),
        ('مشخصات ظاهری', {'fields': ('vehicle_model', 'vehicle_year', 'vehicle_color')}),
        ('مدارک', {'fields': ('plate_number', 'plate_image', 'license_number')}),
        ('ابعاد بنر', {'fields': ('banner_max_width_cm', 'banner_max_height_cm')}),
        ('وضعیت', {'fields': ('is_active', 'created_at', 'updated_at')}),
    )

    def hourly_rate(self, obj):
        return obj.hourly_rate
    hourly_rate.short_description = 'نرخ ساعتی'