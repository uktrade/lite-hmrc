# Generated by Django 2.2.8 on 2020-01-27 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0005_auto_20200127_1440"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mail",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("reply_pending", "Reply Pending"),
                    ("reply_received", "Reply Received"),
                    ("reply_sent", "Reply Sent"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]