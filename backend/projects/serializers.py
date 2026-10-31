from rest_framework import serializers

from workspaces.models import Membership

from .models import Project, ProjectMember


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "key", "description", "status", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_key(self, value):
        if self.instance is not None:
            if value != self.instance.key:
                raise serializers.ValidationError("The project key cannot be changed.")
            return value
        ws_id = self.context["request"].membership.workspace_id
        if Project.objects.filter(workspace_id=ws_id, key=value).exists():
            raise serializers.ValidationError("A project with this key already exists.")
        return value


class ProjectMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    membership_id = serializers.PrimaryKeyRelatedField(
        queryset=Membership.objects.none(), write_only=True, source="workspace_membership")

    class Meta:
        model = ProjectMember
        fields = ["id", "user_id", "email", "membership_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is not None and hasattr(request, "membership"):
            self.fields["membership_id"].queryset = Membership.objects.filter(
                workspace_id=request.membership.workspace_id)

    def validate(self, attrs):
        project = self.context["project"]
        user = attrs["workspace_membership"].user
        if ProjectMember.objects.filter(project=project, user=user).exists():
            raise serializers.ValidationError({"membership_id": "Already a project member."})
        return attrs

    def create(self, validated_data):
        user = validated_data.pop("workspace_membership").user
        return ProjectMember.objects.create(user=user, **validated_data)
