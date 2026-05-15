from rest_framework import permissions


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