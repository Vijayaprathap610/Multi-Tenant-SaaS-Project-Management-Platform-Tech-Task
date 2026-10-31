from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (AcceptInvitationView, InvitationDetailView, InvitationListCreateView,
                    MemberDetailView, MemberListView, WorkspaceViewSet)

router = DefaultRouter()
router.register("workspaces", WorkspaceViewSet, basename="workspace")

urlpatterns = router.urls + [
    path("workspaces/<uuid:workspace_id>/members/", MemberListView.as_view(), name="workspace-members"),
    path("workspaces/<uuid:workspace_id>/members/<uuid:member_id>/", MemberDetailView.as_view(),
         name="workspace-member"),
    path("workspaces/<uuid:workspace_id>/invitations/", InvitationListCreateView.as_view(),
         name="workspace-invitations"),
    path("workspaces/<uuid:workspace_id>/invitations/<uuid:pk>/", InvitationDetailView.as_view(),
         name="workspace-invitation"),
    path("invitations/accept/", AcceptInvitationView.as_view(), name="invitation-accept"),
]
