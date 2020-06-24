# Generated by Django 2.2.13 on 2020-06-24 13:26

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import jsonfield.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Mail",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("edi_filename", models.TextField(blank=True, null=True)),
                ("edi_data", models.TextField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
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
                (
                    "extract_type",
                    models.CharField(
                        choices=[
                            ("usage_update", "Usage update"),
                            ("usage_reply", "Usage Reply"),
                            ("licence_update", "Licence Update"),
                            ("licence_reply", "Licence Reply"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                ("sent_filename", models.TextField(blank=True, null=True)),
                ("sent_data", models.TextField(blank=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("response_filename", models.TextField(blank=True, null=True)),
                ("response_data", models.TextField(blank=True, null=True)),
                ("response_date", models.DateTimeField(blank=True, null=True)),
                ("response_subject", models.TextField(blank=True, null=True)),
                ("sent_response_filename", models.TextField(blank=True, null=True)),
                ("sent_response_data", models.TextField(blank=True, null=True)),
                ("raw_data", models.TextField()),
                ("currently_processing_at", models.DateTimeField(null=True)),
                ("currently_processed_by", models.CharField(max_length=100, null=True)),
                ("retry", models.BooleanField(default=False)),
            ],
            options={"db_table": "mail", "ordering": ["created_at"],},
        ),
        migrations.CreateModel(
            name="OrganisationIdMapping",
            fields=[
                ("lite_id", models.CharField(max_length=36, unique=True)),
                ("rpa_trader_id", models.AutoField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name="UsageUpdate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("licence_ids", models.TextField()),
                ("spire_run_number", models.IntegerField()),
                ("hmrc_run_number", models.IntegerField()),
                ("has_lite_data", models.NullBooleanField(default=None)),
                ("lite_payload", jsonfield.fields.JSONField(default=dict)),
                ("lite_sent_at", models.DateTimeField(blank=True, null=True)),
                ("lite_accepted_licences", jsonfield.fields.JSONField(default=dict)),
                ("lite_rejected_licences", jsonfield.fields.JSONField(default=dict)),
                ("spire_accepted_licences", jsonfield.fields.JSONField(default=dict)),
                ("spire_rejected_licences", jsonfield.fields.JSONField(default=dict)),
                ("lite_licences", jsonfield.fields.JSONField(default=dict)),
                ("spire_licences", jsonfield.fields.JSONField(default=dict)),
                ("mail", models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to="mail.Mail")),
            ],
        ),
        migrations.CreateModel(
            name="LicenceUpdate",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("licence_ids", models.TextField()),
                ("hmrc_run_number", models.IntegerField()),
                ("source_run_number", models.IntegerField(null=True)),
                (
                    "source",
                    models.CharField(choices=[("SPIRE", "SPIRE"), ("LITE", "LITE"), ("HMRC", "HMRC")], max_length=10),
                ),
                ("mail", models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to="mail.Mail")),
            ],
        ),
        migrations.CreateModel(
            name="LicencePayload",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("lite_id", models.CharField(max_length=36)),
                ("reference", models.CharField(max_length=35)),
                ("action", models.CharField(choices=[("insert", "Insert"), ("cancel", "Cancel")], max_length=6)),
                ("data", jsonfield.fields.JSONField(default=dict)),
                ("received_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("is_processed", models.BooleanField(default=False)),
            ],
            options={"unique_together": {("lite_id", "action")},},
        ),
        migrations.CreateModel(
            name="GoodIdMapping",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("lite_id", models.CharField(max_length=36)),
                ("licence_reference", models.CharField(max_length=35)),
                ("line_number", models.PositiveIntegerField()),
            ],
            options={"unique_together": {("lite_id", "licence_reference")},},
        ),
    ]
