from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Q


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        # is_platform_admin can never be set through the public path.
        extra.pop("is_platform_admin", None)
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_platform_admin(self, email, password):
        user = self.model(email=self.normalize_email(email).lower(),
                          is_platform_admin=True)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    # Never exposed by any serializer; set only by create_platform_admin.
    is_platform_admin = models.BooleanField(default=False, editable=False)
    designation = models.CharField(max_length=100, blank=True, default="")
    contact_number = models.CharField(max_length=30, blank=True, default="")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        constraints = [
            # Database-level guarantee: at most one active Platform Administrator.
            models.UniqueConstraint(
                fields=["is_platform_admin"],
                condition=Q(is_platform_admin=True, is_active=True),
                name="single_active_platform_admin",
            ),
        ]
