# Generated by Django 4.2.14 on 2025-01-08 15:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("custom_code", "0002_tidesclass_remove_tidestarget_example_bool_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tidestarget",
            name="auto_tidesclass",
            field=models.CharField(
                blank=True,
                choices=[
                    ("SN", "SN"),
                    ("SNI", "SNI"),
                    ("SNIa", "SNIa"),
                    ("SNIbc", "SNIbc"),
                    ("SNIb", "SNIb"),
                    ("SNIc", "SNIc"),
                    ("SNId", "SNId"),
                    ("SNIe", "SNIe"),
                    ("SNII", "SNII"),
                    ("SLSN-I", "SLSN-I"),
                    ("SLSN-II", "SLSN-II"),
                    ("TDE", "TDE"),
                    ("KN", "KN"),
                    ("AGN", "AGN"),
                    ("LRN", "LRN"),
                    ("CV", "CV"),
                    ("LBV", "LBV"),
                    ("Other", "Other"),
                ],
                max_length=50,
                null=True,
                verbose_name="Auto TiDES Classification",
            ),
        ),
        migrations.AddField(
            model_name="tidestarget",
            name="auto_tidesclass_other",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name="Auto TiDES Classification (Other)",
            ),
        ),
        migrations.AddField(
            model_name="tidestarget",
            name="auto_tidesclass_subclass",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="auto_subclass",
                to="custom_code.tidesclasssubclass",
                verbose_name="Auto TiDES Sub-classification",
            ),
        ),
        migrations.AddField(
            model_name="tidestarget",
            name="human_tidesclass",
            field=models.CharField(
                blank=True,
                choices=[
                    ("SN", "SN"),
                    ("SNI", "SNI"),
                    ("SNIa", "SNIa"),
                    ("SNIbc", "SNIbc"),
                    ("SNIb", "SNIb"),
                    ("SNIc", "SNIc"),
                    ("SNId", "SNId"),
                    ("SNIe", "SNIe"),
                    ("SNII", "SNII"),
                    ("SLSN-I", "SLSN-I"),
                    ("SLSN-II", "SLSN-II"),
                    ("TDE", "TDE"),
                    ("KN", "KN"),
                    ("AGN", "AGN"),
                    ("LRN", "LRN"),
                    ("CV", "CV"),
                    ("LBV", "LBV"),
                    ("Other", "Other"),
                ],
                max_length=50,
                null=True,
                verbose_name="Human TiDES Classification",
            ),
        ),
        migrations.AddField(
            model_name="tidestarget",
            name="human_tidesclass_other",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name="Human TiDES Classification (Other)",
            ),
        ),
        migrations.AddField(
            model_name="tidestarget",
            name="human_tidesclass_subclass",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="human_subclass",
                to="custom_code.tidesclasssubclass",
                verbose_name="Human TiDES Sub-classification",
            ),
        ),
    ]
