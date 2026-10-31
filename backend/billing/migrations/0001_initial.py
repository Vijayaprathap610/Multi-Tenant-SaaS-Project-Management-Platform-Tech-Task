from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('workspaces', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeEvent',
            fields=[
                ('id', models.CharField(max_length=80, primary_key=True, serialize=False)),
                ('type', models.CharField(max_length=80)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('plan', models.CharField(default='free', max_length=20)),
                ('status', models.CharField(default='inactive', max_length=30)),
                ('stripe_customer_id', models.CharField(blank=True, max_length=64)),
                ('stripe_subscription_id', models.CharField(blank=True, max_length=64)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('cancel_at_period_end', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('workspace', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='workspaces.workspace')),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(condition=models.Q(('stripe_customer_id', ''), _negated=True), fields=('stripe_customer_id',), name='unique_stripe_customer'),
                ],
            },
        ),
    ]
