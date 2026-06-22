from rest_framework import permissions
from accounts.models import User


class IsClientUser(permissions.BasePermission):
    """
    کاربری که پروفایل Client دارد.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'client_profile')

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and hasattr(request.user, 'client_profile')


class IsDriverUser(permissions.BasePermission):
    """
    کاربری که پروفایل Driver دارد.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'driver_profile')

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and hasattr(request.user, 'driver_profile')


class IsPrintShopUser(permissions.BasePermission):
    """اجازه فقط به کاربران دارای نقش PRINT_SHOP یا ادمین"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or
            getattr(request.user, 'role', None) == User.Role.PRINT_SHOP
        )
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (
                request.user.is_staff or
                getattr(request.user, 'role', None) == User.Role.PRINT_SHOP
        )


class IsPrintShopOrAdmin(permissions.BasePermission):
    """
    دسترسی برای کاربران ادمین یا کاربرانی که نقش PrintShop دارند.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # ادمین باشد یا نقش CLIENT داشته باشد
        return request.user.is_staff or request.user.role == User.Role.PRINT_SHOP


class IsClientOrAdmin(permissions.BasePermission):
    """
    دسترسی برای کاربران ادمین یا کاربرانی که نقش CLIENT دارند.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # ادمین باشد یا نقش CLIENT داشته باشد
        return request.user.is_staff or request.user.role == 'CLIENT'


class IsDriverOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.role == 'DRIVER'


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    آبجکت متعلق به کاربر باشد (با فیلدهای common: user, driver, client)
    یا کاربر ادمین باشد.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # چک کردن ownerهای مختلف
        if hasattr(obj, 'client') and obj.client == request.user:
            return True
        if hasattr(obj, 'driver') and obj.driver == request.user:
            return True
        if hasattr(obj, 'print-shot') and obj.print_shop == request.user:
            return True
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_staff


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff

