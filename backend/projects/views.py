from django.db import transaction
from rest_framework.generics import (DestroyAPIView, ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView)
from rest_framework.permissions import IsAuthenticated

from audit.services import record
from billing.services import enforce_limit
from tenancy.mixins import TenantScopedMixin
from workspaces.models import ALL_ROLES, MANAGE_ROLES, Role

from .mixins import ProjectScopedMixin
from .models import Project, ProjectMember
from .permissions import ProjectAccessPermission
from .serializers import ProjectMemberSerializer, ProjectSerializer
from .services import create_project_defaults

PM_UP = MANAGE_ROLES | {Role.PROJECT_MANAGER.value}


class ProjectListCreateView(TenantScopedMixin, ListCreateAPIView):
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    required_roles = {"GET": ALL_ROLES, "POST": MANAGE_ROLES}

    def get_queryset(self):
        qs = super().get_queryset()
        m = self.request.membership
        if m.role not in MANAGE_ROLES:  # PMs / Members only see projects they belong to
            qs = qs.filter(members__user_id=m.user_id)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        q = self.request.query_params.get("q")
        if q:
            qs = qs.filter(name__icontains=q)
        return qs.order_by("name", "pk")

    @transaction.atomic
    def perform_create(self, serializer):
        ws = self.request.membership.workspace
        enforce_limit(ws, "projects")
        project = serializer.save(workspace=ws, created_by=self.request.user)
        ProjectMember.objects.create(workspace=ws, project=project, user=self.request.user)
        create_project_defaults(project)
        record("project.created", actor=self.request.user, workspace=ws, resource=project,
               metadata={"key": project.key})


class ProjectDetailView(TenantScopedMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    permission_classes = [IsAuthenticated, ProjectAccessPermission]
    lookup_url_kwarg = "project_id"
    required_roles = {"GET": ALL_ROLES, "PATCH": PM_UP, "DELETE": MANAGE_ROLES}

    def perform_update(self, serializer):
        project = serializer.save()
        record("project.updated", actor=self.request.user, workspace=project.workspace,
               resource=project, metadata={"fields": sorted(serializer.validated_data)})

    def perform_destroy(self, instance):
        record("project.deleted", actor=self.request.user, workspace=instance.workspace,
               metadata={"key": instance.key, "project_id": str(instance.pk)})
        instance.delete()


class ProjectMemberListCreateView(ProjectScopedMixin, ListCreateAPIView):
    serializer_class = ProjectMemberSerializer
    queryset = ProjectMember.objects.select_related("user").order_by("created_at")
    required_roles = {"GET": ALL_ROLES, "POST": PM_UP}

    def perform_create(self, serializer):
        super().perform_create(serializer)
        pm = serializer.instance
        record("project.member_added", actor=self.request.user, workspace=pm.workspace,
               resource=pm, metadata={"project_id": str(pm.project_id)})


class ProjectMemberDetailView(ProjectScopedMixin, DestroyAPIView):
    queryset = ProjectMember.objects.all()
    required_roles = {"DELETE": PM_UP}

    def perform_destroy(self, instance):
        record("project.member_removed", actor=self.request.user, workspace=instance.workspace,
               resource=instance, metadata={"project_id": str(instance.project_id)})
        instance.delete()
