from rest_framework import serializers

from .models import WorkflowStatus, WorkflowTransition


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStatus
        fields = ["id", "name", "category", "position"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        qs = WorkflowStatus.objects.filter(project=self.context["project"], name__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A status with this name already exists.")
        return value


class TransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTransition
        fields = ["id", "from_status", "to_status"]
        read_only_fields = ["id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project")
        if project is not None:  # ids from other projects/tenants are simply "invalid"
            qs = WorkflowStatus.objects.filter(project=project)
            self.fields["from_status"].queryset = qs
            self.fields["to_status"].queryset = qs

    def validate(self, attrs):
        if attrs["from_status"] == attrs["to_status"]:
            raise serializers.ValidationError("A transition must connect two different statuses.")
        if WorkflowTransition.objects.filter(from_status=attrs["from_status"],
                                             to_status=attrs["to_status"]).exists():
            raise serializers.ValidationError("This transition already exists.")
        return attrs
