from django.contrib import admin
from .models import Trip

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'driver', 'campaign', 'vehicle', 'status', 'start_time', 'earnings']
    list_filter = ['status', 'campaign']
    search_fields = ['driver__email', 'campaign__title', 'vehicle__plate_number']
    readonly_fields = ['snapshot', 'created_at', 'updated_at']
    fieldsets = (
        ('اطلاعات اصلی', {'fields': ('driver', 'campaign', 'vehicle', 'status')}),
        ('زمان‌ها', {'fields': ('start_time', 'end_time')}),
        ('مالی', {'fields': ('total_active_seconds', 'total_distance_km', 'earnings')}),
        ('اسنپ‌شات', {'fields': ('snapshot',)}),
        ('زیرساخت', {'fields': ('created_at', 'updated_at')}),
    )