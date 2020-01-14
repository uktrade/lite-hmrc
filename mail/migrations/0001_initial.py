# Generated by Django 2.2.8 on 2020-01-14 14:35

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
                ("edi_filename", models.TextField(blank=True, null=True)),
                ("edi_data", models.TextField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("accepted", "Accepted")], max_length=20, null=True
                    ),
                ),
                (
                    "extract_type",
                    models.CharField(
                        choices=[("insert", "Insert")], max_length=20, null=True
                    ),
                ),
                ("response_file", models.TextField(blank=True, null=True)),
                ("response_date", models.DateTimeField(blank=True, null=True)),
                ("raw_data", models.TextField()),
                ("serializer_errors", models.TextField(blank=True, null=True)),
                ("errors", models.TextField(blank=True, null=True)),
            ],
            options={"ordering": ["created_at"],},
        ),
        migrations.CreateModel(
            name="LicenceUsage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("license_ids", models.TextField()),
                (
                    "mail",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING, to="mail.Mail"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LicenceUpdate",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("license_ids", models.TextField()),
                ("hmrc_run_number", models.IntegerField()),
                ("source_run_number", models.IntegerField(null=True)),
                (
                    "source",
                    models.CharField(
                        choices=[("SPIRE", "SPIRE"), ("LITE", "LITE")], max_length=10
                    ),
                ),
                (
                    "mail",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING, to="mail.Mail"
                    ),
                ),
            ],
        ),
    ]
