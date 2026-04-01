from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="company_logo",
            field=models.ImageField(blank=True, upload_to="branding/", verbose_name="Firmenlogo"),
        ),
    ]
