from rest_framework import serializers

from .models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(source="uploaded_by.email", read_only=True, default=None)

    class Meta:
        model = Attachment
        fields = ["id", "original_name", "content_type", "size", "uploaded_by_email", "created_at"]
        read_only_fields = fields  # storage path and hash are never exposed
