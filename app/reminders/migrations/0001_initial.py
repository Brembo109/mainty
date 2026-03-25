import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")),
                ("notification_type", models.CharField(choices=[("upcoming", "Erinnerung vor Fälligkeit"), ("overdue", "Überfälligkeits-Eskalation"), ("digest_daily", "Tägliche Zusammenfassung"), ("digest_weekly", "Wöchentliche Zusammenfassung")], max_length=20, verbose_name="Typ")),
                ("object_id", models.CharField(blank=True, max_length=64, verbose_name="Objekt-ID")),
                ("recipient_email", models.EmailField(max_length=254, verbose_name="Empfänger E-Mail")),
                ("subject", models.CharField(blank=True, max_length=255, verbose_name="Betreff")),
                ("status", models.CharField(choices=[("success", "Erfolgreich"), ("failed", "Fehlgeschlagen")], default="success", max_length=20, verbose_name="Status")),
                ("sent_at", models.DateTimeField(auto_now_add=True, verbose_name="Gesendet am")),
                ("period_key", models.CharField(blank=True, max_length=32, verbose_name="Periodenschlüssel")),
                ("error_message", models.TextField(blank=True, verbose_name="Fehlermeldung")),
                ("content_type", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="contenttypes.contenttype", verbose_name="Objekttyp")),
                ("recipient_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notification_logs", to=settings.AUTH_USER_MODEL, verbose_name="Empfänger")),
            ],
            options={
                "verbose_name": "Benachrichtigungsprotokoll",
                "verbose_name_plural": "Benachrichtigungsprotokolle",
                "ordering": ["-sent_at", "-id"],
            },
        ),
    ]
