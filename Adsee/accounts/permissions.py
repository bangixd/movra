from rest_framework import permissions

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