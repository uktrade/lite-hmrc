# Generated by Django 2.2.8 on 2020-01-27 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0004_auto_20200127_1320"),
    ]

    operations = [
        migrations.RenameField(model_name="mail", old_name="response_file", new_name="response_data",),
        migrations.AddField(
            model_name="mail", name="response_filename", field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="licenceupdate",
            name="source",
            field=models.CharField(choices=[("SPIRE", "SPIRE"), ("LITE", "LITE"), ("HMRC", "HMRC")], max_length=10,),
        ),
    ]
