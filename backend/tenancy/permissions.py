from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import BasePermission

from workspaces.models import Membership


class WorkspaceMembershipPermission(BasePermission):
    """Resolves the caller's membership for URL kwarg `workspace_id` on the server.

    * Not a member (or workspace does not exist) -> 404, so existence is not leaked.
    * Member without a sufficient role -> 403.
    * Views must declare `required_roles = {"GET": {...}, "POST": {...}}`;
      any HTTP method not listed is denied (secure default).
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        membership = (Membership.objects.select_related("workspace")
                      .filter(user=user, workspace_id=view.kwargs["workspace_id"]).first())
        if membership is None:
            raise NotFound()
        allowed = getattr(view, "required_roles", {}).get(request.method)
        if not allowed or membership.role not in allowed:
            raise PermissionDenied()
        request.membership = membership
        return True
