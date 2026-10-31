from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    issue_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "event_type", "message", "issue_id", "project_id", "read_at", "created_at"]
        read_only_fields = fields
