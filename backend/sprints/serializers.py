from rest_framework import serializers

from .models import Sprint, SprintStatus


class SprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sprint
        fields = ["id", "name", "goal", "start_date", "end_date", "status", "completed_at", "created_at"]
        read_only_fields = ["id", "status", "completed_at", "created_at"]  # status changes via start/complete

    def validate(self, attrs):
        if self.instance is not None and self.instance.status == SprintStatus.COMPLETED:
            raise serializers.ValidationError("A completed sprint cannot be edited.")
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date must not be before the start date."})
        return attrs


class CompleteSprintSerializer(serializers.Serializer):
    move_incomplete_to = serializers.PrimaryKeyRelatedField(
        queryset=Sprint.objects.none(), allow_null=True, required=False, default=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project")
        if project is not None:
            self.fields["move_incomplete_to"].queryset = Sprint.objects.filter(
                project=project, status=SprintStatus.PLANNED)


class AssignIssuesSerializer(serializers.Serializer):
    issue_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=200)
