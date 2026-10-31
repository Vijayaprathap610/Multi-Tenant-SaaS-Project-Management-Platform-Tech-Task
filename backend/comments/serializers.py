from rest_framework import serializers

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True, default=None)
    body = serializers.CharField(max_length=5000)

    class Meta:
        model = Comment
        fields = ["id", "author_email", "body", "created_at", "updated_at", "edited_at"]
        read_only_fields = ["id", "created_at", "updated_at", "edited_at"]

    def validate_body(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Comment cannot be empty.")
        return value
