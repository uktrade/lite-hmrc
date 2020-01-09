# Generated by Django 2.2.8 on 2020-01-09 12:29

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Mail",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_submitted_on", models.DateTimeField(blank=True, null=True)),
                ("edi_data", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[("accepted", "Accepted")], max_length=20, null=True
                    ),
                ),
                (
                    "extract_type",
                    models.CharField(choices=[("insert", "Insert")], max_length=20),
                ),
                ("response_file", models.TextField(blank=True, null=True)),
                ("response_date", models.DateTimeField(blank=True, null=True)),
                ("edi_filename", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="LicenseUpdate",
            fields=[
                (
                    "mail_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="mail.Mail",
                    ),
                ),
                ("license_id", models.UUIDField()),
                ("hmrc_run_number", models.IntegerField()),
                ("source_run_number", models.IntegerField(null=True)),
                (
                    "source",
                    models.CharField(
                        choices=[("SPIRE", "SPIRE"), ("LITE", "LITE")], max_length=10
                    ),
                ),
            ],
            bases=("mail.mail",),
        ),
        migrations.CreateModel(
            name="LicenseUsage",
            fields=[
                (
                    "mail_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="mail.Mail",
                    ),
                ),
            ],
            bases=("mail.mail",),
        ),
    ]
