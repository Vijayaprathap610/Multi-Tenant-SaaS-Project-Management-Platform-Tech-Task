from django.db import migrations


def add_user_columns(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        cursor.execute("""
            ALTER TABLE "accounts_user"
            ADD COLUMN IF NOT EXISTS "designation" varchar(100) NOT NULL DEFAULT '';
            ALTER TABLE "accounts_user"
            ADD COLUMN IF NOT EXISTS "contact_number" varchar(30) NOT NULL DEFAULT '';
        """)
    else:
        cursor.execute("PRAGMA table_info(accounts_user)")
        columns = [row[1] for row in cursor.fetchall()]
        if "designation" not in columns:
            cursor.execute('ALTER TABLE "accounts_user" ADD COLUMN "designation" varchar(100) NOT NULL DEFAULT ""')
        if "contact_number" not in columns:
            cursor.execute('ALTER TABLE "accounts_user" ADD COLUMN "contact_number" varchar(30) NOT NULL DEFAULT ""')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_user_columns, reverse_code=migrations.RunPython.noop),
    ]

