from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import User
from accounts.forms import UserCreationForm, UserChangeForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("phone", "role", "is_staff", "is_active", "created_at")
    list_filter = ("role", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("phone",)}),
        ("Permissions", {"fields": ("role", "is_staff", "is_active", "is_superuser")}),
        ("Important dates", {"fields": ("created_at",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "role"),
        }),
    )

    search_fields = ("phone",)
    ordering = ("phone",)
    readonly_fields = ("created_at",)


