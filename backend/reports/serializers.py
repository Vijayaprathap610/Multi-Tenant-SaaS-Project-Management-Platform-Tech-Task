from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "status", "data", "error", "created_at", "completed_at"]
        read_only_fields = fields
