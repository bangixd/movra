from django.contrib import admin
from .models import PrintShopProfile

@admin.register(PrintShopProfile)
class PrintShopProfileAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'user', 'phone', 'is_active']
    search_fields = ['shop_name', 'user__phone']