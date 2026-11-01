import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Workspace',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
                ('slug', models.SlugField(max_length=60, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('owner', 'Workspace Owner'), ('admin', 'Workspace Administrator'), ('project_manager', 'Project Manager'), ('member', 'Developer / Team Member')], max_length=20)),
                ('designation', models.CharField(blank=True, default='', max_length=100)),
                ('contact_number', models.CharField(blank=True, default='', max_length=30)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='workspaces.workspace')),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('workspace', 'user'), name='unique_membership'),
                ],
                'indexes': [
                    models.Index(fields=['user', 'workspace'], name='workspaces__user_id_1b1ebf_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254)),
                ('role', models.CharField(choices=[('owner', 'Workspace Owner'), ('admin', 'Workspace Administrator'), ('project_manager', 'Project Manager'), ('member', 'Developer / Team Member')], max_length=20)),
                ('designation', models.CharField(blank=True, default='', max_length=100)),
                ('contact_number', models.CharField(blank=True, default='', max_length=30)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('invited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='workspaces.workspace')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['workspace', 'email'], name='workspaces__workspa_920614_idx'),
                ],
            },
        ),
    ]

