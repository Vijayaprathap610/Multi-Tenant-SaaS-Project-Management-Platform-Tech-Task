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
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "email", "role", "created_at"]
        read_only_fields = fields


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
