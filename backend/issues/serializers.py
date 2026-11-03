from django.contrib.auth import get_user_model
from rest_framework import serializers

from projects.access import user_has_project_access
from sprints.models import Sprint, SprintStatus
from workflows.models import WorkflowStatus
from workspaces.models import Membership

from .models import Issue
from .services import check_transition

User = get_user_model()


class IssueBriefSerializer(serializers.ModelSerializer):
    key = serializers.CharField(read_only=True)
    assignee_email = serializers.EmailField(source="assignee.email", read_only=True, default=None)
    status_id = serializers.UUIDField(read_only=True)
    status_name = serializers.CharField(source="status.name", read_only=True, default="")

    class Meta:
        model = Issue
        fields = ["id", "key", "title", "priority", "status_id", "status_name", "assignee", "assignee_email",
                  "sprint", "labels", "due_date", "position"]
        read_only_fields = fields


class IssueSerializer(serializers.ModelSerializer):
    key = serializers.CharField(read_only=True)
    reporter_email = serializers.EmailField(source="reporter.email", read_only=True, default=None)
    assignee_email = serializers.EmailField(source="assignee.email", read_only=True, default=None)
    status = serializers.PrimaryKeyRelatedField(queryset=WorkflowStatus.objects.none(), required=False)
    status_name = serializers.CharField(source="status.name", read_only=True, default="")
    assignee = serializers.PrimaryKeyRelatedField(queryset=User.objects.none(), allow_null=True,
                                                  required=False)
    sprint = serializers.PrimaryKeyRelatedField(queryset=Sprint.objects.none(), allow_null=True,
                                                required=False)
    labels = serializers.ListField(child=serializers.CharField(max_length=30), max_length=10,
                                   required=False)

    class Meta:
        model = Issue
        fields = ["id", "key", "number", "title", "description", "status", "status_name", "priority", "assignee",
                  "assignee_email", "reporter_email", "sprint", "labels", "due_date", "position", "created_at",
                  "updated_at"]
        read_only_fields = ["id", "number", "position", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project")
        if project is None:
            return
        # Every foreign key the client can send is limited to this project / workspace, so ids
        # belonging to another project or tenant fail as "invalid pk" and reveal nothing.
        self.fields["status"].queryset = WorkflowStatus.objects.filter(project=project)
        self.fields["sprint"].queryset = Sprint.objects.filter(project=project)
        self.fields["assignee"].queryset = User.objects.filter(
            memberships__workspace_id=project.workspace_id)

    def validate_assignee(self, user):
        if user is not None and not user_has_project_access(user.pk, self.context["project"]):
            raise serializers.ValidationError("Assignee does not have access to this project.")
        return user

    def validate_sprint(self, sprint):
        if sprint is not None and sprint.status == SprintStatus.COMPLETED:
            raise serializers.ValidationError("Cannot assign issues to a completed sprint.")
        return sprint

    def validate(self, attrs):
        new_status = attrs.get("status")
        if self.instance is not None and new_status is not None:
            check_transition(self.context["project"], self.instance.status, new_status)
        return attrs


class MoveSerializer(serializers.Serializer):
    status = serializers.PrimaryKeyRelatedField(queryset=WorkflowStatus.objects.none())
    before_issue_id = serializers.UUIDField(allow_null=True, required=False, default=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project")
        if project is not None:
            self.fields["status"].queryset = WorkflowStatus.objects.filter(project=project)
