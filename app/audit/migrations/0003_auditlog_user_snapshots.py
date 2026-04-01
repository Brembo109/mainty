from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_rename_audit_audit_model_n_0e10c0_idx_audit_audit_model_n_20c0d3_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="user_display_snapshot",
            field=models.CharField(blank=True, max_length=255, verbose_name="Benutzeranzeige"),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="user_role_snapshot",
            field=models.CharField(blank=True, max_length=50, verbose_name="Benutzerrolle"),
        ),
    ]
