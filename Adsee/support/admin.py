from django.contrib import admin
from .models import SiteSetting, Ticket, FAQCategory, FAQItem


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ('اطلاعات برند', {
            'fields': ('brand_name', 'brand_logo', 'about_text', 'about_image')
        }),
        ('راه‌های ارتباطی', {
            'fields': ('phone', 'email', 'address')
        }),
        ('شبکه‌های اجتماعی', {
            'fields': ('social_links',),
            'description': 'یک دیکشنری JSON وارد کنید، مثال: {"instagram": "https://instagram.com/..."}'
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )
    list_display = ['brand_name', 'phone', 'email', 'is_active']

    # جلوگیری از ایجاد بیش از یک رکورد (حالت Singleton)
    def has_add_permission(self, request):
        # اگر از قبل یک رکورد وجود داشت، اجازهٔ افزودن جدید نده
        return not SiteSetting.objects.exists()


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'phone', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['subject', 'user__phone', 'name']


@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']

@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active']
    list_filter = ['category']