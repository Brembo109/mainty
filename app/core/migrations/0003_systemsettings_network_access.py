from django.db import migrations, models

import core.models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_systemsettings_company_logo"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="allowed_hosts",
            field=models.TextField(blank=True, default=core.models.default_allowed_hosts, verbose_name="Allowed Hosts"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="app_public_url",
            field=models.URLField(blank=True, verbose_name="Öffentliche URL"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="csrf_trusted_origins",
            field=models.TextField(
                blank=True,
                default=core.models.default_csrf_trusted_origins,
                verbose_name="CSRF Trusted Origins",
            ),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="debug_mode",
            field=models.BooleanField(default=core.models.default_debug_mode, verbose_name="Debug-Modus"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="force_https",
            field=models.BooleanField(default=core.models.default_force_https, verbose_name="HTTPS erzwingen"),
        ),
    ]
