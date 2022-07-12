# Generated by Django 3.2.14 on 2022-07-14 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0017_auto_20220517_0830"),
    ]

    operations = [
        migrations.AlterField(
            model_name="licencepayload",
            name="data",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="usagedata",
            name="licence_ids",
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name="usagedata",
            name="lite_accepted_licences",
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name="usagedata",
            name="lite_licences",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="usagedata",
            name="lite_payload",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="usagedata",
            name="lite_rejected_licences",
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name="usagedata",
            name="lite_response",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="usagedata",
            name="spire_accepted_licences",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="usagedata",
            name="spire_licences",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="usagedata",
            name="spire_rejected_licences",
            field=models.JSONField(default=dict),
        ),
    ]
