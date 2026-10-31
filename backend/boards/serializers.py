from rest_framework import serializers

from workflows.models import WorkflowStatus

from .models import Board, BoardColumn


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardColumn
        fields = ["id", "name", "status", "position"]
        read_only_fields = ["id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.context.get("project")
        if project is not None:
            self.fields["status"].queryset = WorkflowStatus.objects.filter(project=project)

    def validate(self, attrs):
        board = self.context.get("board")
        status = attrs.get("status")
        if board is not None and status is not None:
            qs = BoardColumn.objects.filter(board=board, status=status)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"status": "This status already has a column."})
        return attrs


class BoardSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "name", "columns", "created_at"]
        read_only_fields = ["id", "created_at"]
