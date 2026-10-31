from django.urls import path

from .views import AuditListView

urlpatterns = [
    path("workspaces/<uuid:workspace_id>/audit/", AuditListView.as_view(), name="workspace-audit"),
]
