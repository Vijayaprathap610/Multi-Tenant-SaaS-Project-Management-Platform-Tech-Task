from rest_framework import serializers

from .models import EVENTS, WebhookDelivery, WebhookEndpoint
from .security import UnsafeTarget, validate_target_url


class EndpointSerializer(serializers.ModelSerializer):
    events = serializers.ListField(child=serializers.ChoiceField(choices=EVENTS + ["*"]), min_length=1)

    class Meta:
        model = WebhookEndpoint
        fields = ["id", "url", "description", "events", "active", "created_at"]  # never `secret`
        read_only_fields = ["id", "created_at"]

    def validate_url(self, value):
        try:
            validate_target_url(value)
        except UnsafeTarget as exc:
            raise serializers.ValidationError(str(exc))
        return value


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDelivery
        fields = ["id", "event_id", "event_type", "status", "attempts", "response_status", "error",
                  "created_at", "delivered_at"]
        read_only_fields = fields
