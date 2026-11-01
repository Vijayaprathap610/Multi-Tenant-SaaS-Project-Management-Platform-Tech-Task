from django.db import migrations


def add_membership_columns(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        cursor.execute("""
            ALTER TABLE "workspaces_membership"
            ADD COLUMN IF NOT EXISTS "designation" varchar(100) NOT NULL DEFAULT '';

            ALTER TABLE "workspaces_membership"
            ADD COLUMN IF NOT EXISTS "contact_number" varchar(30) NOT NULL DEFAULT '';

            ALTER TABLE "workspaces_membership"
            ADD COLUMN IF NOT EXISTS "is_active" boolean NOT NULL DEFAULT TRUE;
        """)
    else:
        cursor.execute("PRAGMA table_info(workspaces_membership)")
        columns = [row[1] for row in cursor.fetchall()]
        if "designation" not in columns:
            cursor.execute('ALTER TABLE "workspaces_membership" ADD COLUMN "designation" varchar(100) NOT NULL DEFAULT ""')
        if "contact_number" not in columns:
            cursor.execute('ALTER TABLE "workspaces_membership" ADD COLUMN "contact_number" varchar(30) NOT NULL DEFAULT ""')
        if "is_active" not in columns:
            cursor.execute('ALTER TABLE "workspaces_membership" ADD COLUMN "is_active" boolean NOT NULL DEFAULT 1')


class Migration(migrations.Migration):

    dependencies = [
        (
            "workspaces",
            "0002_rename_workspaces__workspa_920614_idx_workspaces__workspa_f56ea8_idx_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(add_membership_columns, reverse_code=migrations.RunPython.noop),
    ]
