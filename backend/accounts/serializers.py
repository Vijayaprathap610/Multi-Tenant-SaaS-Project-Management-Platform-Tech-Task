from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate(self, attrs):
        attrs["email"] = attrs["email"].strip().lower()
        validate_password(attrs["password"], user=User(email=attrs["email"]))
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(trim_whitespace=False)


class MeSerializer(serializers.ModelSerializer):
    memberships = serializers.SerializerMethodField()
    is_platform_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "designation", "contact_number", "is_platform_admin", "memberships"]
        read_only_fields = fields

    def get_memberships(self, user):
        return [{"workspace_id": str(m.workspace_id), "workspace_name": m.workspace.name,
                 "role": m.role, "designation": m.designation, "contact_number": m.contact_number,
                 "is_active": m.is_active}
                for m in user.memberships.select_related("workspace").order_by("workspace__name")]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(trim_whitespace=False)
    new_password = serializers.CharField(trim_whitespace=False)
