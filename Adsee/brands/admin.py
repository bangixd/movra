from django.contrib import admin
from django.utils.html import format_html
from .models import Brand


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['logo_preview', 'name', 'client', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'client__email', 'client__first_name', 'client__last_name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'logo_preview_large']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('client', 'name', 'slug', 'description', 'website')
        }),
        ('لوگو', {
            'fields': ('logo', 'logo_preview_large'),
        }),
        ('وضعیت', {
            'fields': ('is_active', 'created_at', 'updated_at'),
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:contain;" />', obj.logo.url)
        return "—"
    logo_preview.short_description = 'پیش‌نمایش لوگو'

    def logo_preview_large(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="200" style="max-height:200px; object-fit:contain;" />', obj.logo.url)
        return "لوگویی آپلود نشده"
    logo_preview_large.short_description = 'پیش‌نمایش بزرگ'