from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("assets", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MaintenanceContract",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")),
                ("title", models.CharField(max_length=255, verbose_name="Titel")),
                ("contract_number", models.CharField(blank=True, max_length=100, verbose_name="Vertragsnummer")),
                ("order_number", models.CharField(blank=True, max_length=100, verbose_name="Auftragsnummer")),
                ("vendor", models.CharField(max_length=255, verbose_name="Dienstleister")),
                ("start_date", models.DateField(verbose_name="Startdatum")),
                ("end_date", models.DateField(verbose_name="Enddatum")),
                ("warning_months", models.PositiveIntegerField(default=3, verbose_name="Vorwarnzeit in Monaten")),
                (
                    "maintenance_frequency",
                    models.CharField(
                        choices=[
                            ("annual", "Jährlich"),
                            ("semi_annual", "Halbjährlich"),
                            ("quarterly", "Quartalsweise"),
                            ("other", "Sonstiges"),
                        ],
                        default="annual",
                        max_length=20,
                        verbose_name="Wartungsintervall",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notizen")),
                (
                    "assets",
                    models.ManyToManyField(blank=True, related_name="contracts", to="assets.asset", verbose_name="Assets"),
                ),
            ],
            options={
                "verbose_name": "Wartungsvertrag",
                "verbose_name_plural": "Wartungsverträge",
                "ordering": ["end_date", "title"],
            },
        ),
    ]

