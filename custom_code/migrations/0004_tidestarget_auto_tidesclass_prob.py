# Generated by Django 4.2.14 on 2025-01-08 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("custom_code", "0003_tidestarget_auto_tidesclass_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tidestarget",
            name="auto_tidesclass_prob",
            field=models.FloatField(
                blank=True,
                null=True,
                verbose_name="Auto TiDES Classification Probability",
            ),
        ),
    ]
