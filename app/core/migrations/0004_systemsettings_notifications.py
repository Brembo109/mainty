from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_systemsettings_network_access"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="maintenance_upcoming_days",
            field=models.PositiveIntegerField(default=7, verbose_name="Vorlaufzeit Wartung in Tagen"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="notification_from_email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="Absender E-Mail"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="notifications_enabled",
            field=models.BooleanField(default=False, verbose_name="Benachrichtigungen aktiviert"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="only_notify_once_per_status",
            field=models.BooleanField(default=False, verbose_name="Nur einmal pro Status benachrichtigen"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="overdue_escalation_days",
            field=models.PositiveIntegerField(default=0, verbose_name="Eskalation bei Überfälligkeit ab Tagen"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="qualification_upcoming_days",
            field=models.PositiveIntegerField(default=14, verbose_name="Vorlaufzeit Qualifizierung in Tagen"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="send_daily_digest",
            field=models.BooleanField(default=False, verbose_name="Tägliche Zusammenfassung senden"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="send_overdue_reminders",
            field=models.BooleanField(default=True, verbose_name="Überfällige Einträge melden"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="send_upcoming_reminders",
            field=models.BooleanField(default=True, verbose_name="Erinnerungen vor Fälligkeit senden"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="send_weekly_digest",
            field=models.BooleanField(default=False, verbose_name="Wöchentliche Zusammenfassung senden"),
        ),
    ]
