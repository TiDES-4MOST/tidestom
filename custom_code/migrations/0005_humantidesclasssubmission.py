# Generated by Django 4.2.14 on 2025-03-26 15:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("custom_code", "0004_tidestarget_auto_tidesclass_prob"),
    ]

    operations = [
        migrations.CreateModel(
            name="HumanTidesClassSubmission",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tidesclass",
                    models.CharField(
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
                        verbose_name="Human TiDES Classification",
                    ),
                ),
                (
                    "tidesclass_other",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Human TiDES Classification (Other)",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="Submission Time",
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="human_classifications",
                        to="custom_code.tidestarget",
                    ),
                ),
                (
                    "tidesclass_subclass",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="custom_code.tidesclasssubclass",
                        verbose_name="Human TiDES Sub-classification",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Submitted By",
                    ),
                ),
            ],
            options={
                "verbose_name": "Human TiDES Classification Submission",
                "verbose_name_plural": "Human TiDES Classification Submissions",
            },
        ),
    ]
