import uuid

from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from .models import INVITABLE_ROLES, Invitation, Membership, Role, Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="my_role", read_only=True)

    class Meta:
        model = Workspace
        fields = ["id", "name", "slug", "role", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        slug = f"{slugify(validated_data['name'])[:40] or 'workspace'}-{uuid.uuid4().hex[:6]}"
        workspace = Workspace.objects.create(slug=slug, created_by=user, **validated_data)
        Membership.objects.create(workspace=workspace, user=user, role=Role.OWNER)
        workspace.my_role = Role.OWNER
        return workspace


class MemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    full_name = serializers.SerializerMethodField()
    assigned_projects = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = [
            "id", "user_id", "email", "first_name", "last_name", "full_name",
            "role", "designation", "contact_number", "is_active", "assigned_projects", "created_at"
        ]
        read_only_fields = ["id", "user_id", "email", "first_name", "last_name", "full_name", "created_at"]

    def get_full_name(self, obj):
        name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return name or obj.user.email.split("@")[0]

    def get_assigned_projects(self, obj):
        return [
            {"id": str(pm.project.id), "name": pm.project.name, "key": pm.project.key}
            for pm in obj.user.project_memberships.filter(workspace_id=obj.workspace_id).select_related("project")
        ]


class CreateMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    role = serializers.ChoiceField(choices=[Role.PROJECT_MANAGER.value, Role.MEMBER.value])
    designation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    contact_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    project_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_email(self, value):
        return value.strip().lower()


class MemberUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=Role.choices, required=False)
    designation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    contact_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    project_ids = serializers.ListField(child=serializers.UUIDField(), required=False)


class RoleChangeSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=Role.choices)


class InvitationSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=[(r.value, r.label) for r in INVITABLE_ROLES])

    class Meta:
        model = Invitation
        fields = ["id", "email", "role", "created_at", "expires_at"]
        read_only_fields = ["id", "created_at", "expires_at"]

    def validate_email(self, value):
        return value.strip().lower()


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)
