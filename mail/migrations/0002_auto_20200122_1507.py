# Generated by Django 2.2.8 on 2020-01-22 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="mail",
            name="currently_processed_by",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="mail",
            name="currently_processing_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name="mail",
            name="extract_type",
            field=models.CharField(
                choices=[("usage_update", "Usage update")], max_length=20, null=True
            ),
        ),
    ]
