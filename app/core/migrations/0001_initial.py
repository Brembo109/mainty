from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SystemSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")),
                ("singleton_enforcer", models.BooleanField(default=True, editable=False, unique=True)),
                (
                    "default_maintenance_warning_days",
                    models.PositiveIntegerField(default=7, verbose_name="Standard Warnungstage Wartung"),
                ),
                (
                    "default_maintenance_interval_value",
                    models.PositiveIntegerField(default=30, verbose_name="Standard Intervallwert Wartung"),
                ),
                (
                    "default_maintenance_interval_unit",
                    models.CharField(
                        choices=[("days", "Tage"), ("weeks", "Wochen"), ("months", "Monate"), ("years", "Jahre")],
                        default="days",
                        max_length=10,
                        verbose_name="Standard Intervall-Einheit Wartung",
                    ),
                ),
                (
                    "default_qualification_warning_days",
                    models.PositiveIntegerField(default=14, verbose_name="Standard Warnungstage Qualifizierung"),
                ),
                (
                    "default_qualification_interval_value",
                    models.PositiveIntegerField(default=12, verbose_name="Standard Intervallwert Qualifizierung"),
                ),
                (
                    "default_qualification_interval_unit",
                    models.CharField(
                        choices=[("days", "Tage"), ("weeks", "Wochen"), ("months", "Monate"), ("years", "Jahre")],
                        default="months",
                        max_length=10,
                        verbose_name="Standard Intervall-Einheit Qualifizierung",
                    ),
                ),
            ],
            options={
                "verbose_name": "Systemeinstellung",
                "verbose_name_plural": "Systemeinstellungen",
            },
        ),
    ]
