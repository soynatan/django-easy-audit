from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("easyaudit", "0019_alter_crudevent_changed_fields_and_more"),
    ]

    operations = [
        # Nullable with no default, so adding it rewrites no rows on any backend.
        migrations.AddField(
            model_name="requestevent",
            name="auth_method",
            field=models.CharField(
                blank=True, max_length=32, null=True, verbose_name="Auth method"
            ),
        ),
    ]
