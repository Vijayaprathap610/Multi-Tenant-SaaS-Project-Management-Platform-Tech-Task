from rest_framework.permissions import BasePermission


class IsPlatformAdmin(BasePermission):
    """Backend-enforced; the flag cannot be set by any API."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u.is_authenticated and u.is_active and u.is_platform_admin)
