# Generated by Django 2.2.13 on 2020-07-10 14:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0002_usageupdate_has_spire_data"),
    ]

    operations = [
        migrations.AlterModelOptions(name="usageupdate", options={"ordering": ["mail__created_at"]},),
    ]
