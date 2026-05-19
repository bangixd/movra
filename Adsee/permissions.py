from rest_framework import permissions
from accounts.models import User


class IsClientUser(permissions.BasePermission):
    """
    کاربری که پروفایل Client دارد.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'client_profile')


class IsDriverUser(permissions.BasePermission):
    """
    کاربری که پروفایل Driver دارد.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'driver_profile')


class IsClientOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or hasattr(request.user, 'client_profile')
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # کلاینت صاحب برند کمپین
        return obj.campaign.brand.client == request.user


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
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_staff


class IsPrintShopUser(permissions.BasePermission):
    """اجازه فقط به کاربران دارای نقش PRINT_SHOP یا ادمین"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or
            getattr(request.user, 'role', None) == User.Role.PRINT_SHOP
        )
