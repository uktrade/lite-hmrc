# Generated by Django 3.2.16 on 2022-11-02 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0018_auto_20220714_1127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='licencepayload',
            name='action',
            field=models.CharField(choices=[('insert', 'Insert'), ('cancel', 'Cancel'), ('update', 'Update'), ('replace', 'Replace')], max_length=7),
        ),
    ]
