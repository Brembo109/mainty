from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="auditlog",
            new_name="audit_audit_model_n_20c0d3_idx",
            old_name="audit_audit_model_n_0e10c0_idx",
        ),
        migrations.RenameIndex(
            model_name="auditlog",
            new_name="audit_audit_timesta_19e18a_idx",
            old_name="audit_audit_timesta_224ca3_idx",
        ),
    ]
