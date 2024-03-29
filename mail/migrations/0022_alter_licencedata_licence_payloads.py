# Generated by Django 4.2.9 on 2024-01-04 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0021_licencepayload_skip_process"),
    ]

    operations = [
        migrations.AlterField(
            model_name="licencedata",
            name="licence_payloads",
            field=models.ManyToManyField(
                help_text="LicencePayload records linked to this LicenceData instance",
                related_name="+",
                to="mail.licencepayload",
            ),
        ),
    ]
