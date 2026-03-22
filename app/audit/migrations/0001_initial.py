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
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("timestamp", models.DateTimeField(auto_now_add=True, verbose_name="Zeitpunkt")),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("create", "Angelegt"),
                            ("update", "Aktualisiert"),
                            ("delete", "Gelöscht"),
                            ("status_change", "Statuswechsel"),
                        ],
                        max_length=20,
                        verbose_name="Aktion",
                    ),
                ),
                ("model_name", models.CharField(db_index=True, max_length=100, verbose_name="Modell")),
                ("object_id", models.CharField(db_index=True, max_length=64, verbose_name="Objekt-ID")),
                ("object_repr", models.CharField(max_length=255, verbose_name="Objekt")),
                ("field_name", models.CharField(blank=True, max_length=100, verbose_name="Feld")),
                ("old_value", models.TextField(blank=True, verbose_name="Alter Wert")),
                ("new_value", models.TextField(blank=True, verbose_name="Neuer Wert")),
                ("change_reason", models.TextField(blank=True, verbose_name="Änderungsgrund")),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Benutzer",
                    ),
                ),
            ],
            options={
                "verbose_name": "Audit-Eintrag",
                "verbose_name_plural": "Audit-Einträge",
                "ordering": ["-timestamp", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["model_name", "object_id"], name="audit_audit_model_n_0e10c0_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["timestamp"], name="audit_audit_timesta_224ca3_idx"),
        ),
    ]
