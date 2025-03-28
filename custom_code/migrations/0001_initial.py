# Generated by Django 4.2.14 on 2024-12-19 16:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tom_targets", "0021_rename_target_basetarget_alter_basetarget_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="TidesTarget",
            fields=[
                (
                    "basetarget_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="tom_targets.basetarget",
                    ),
                ),
                (
                    "example_bool",
                    models.BooleanField(default=False, verbose_name="Example Boolean"),
                ),
                (
                    "example_number",
                    models.FloatField(
                        blank=True, help_text="Pick a number.", null=True
                    ),
                ),
            ],
            options={
                "verbose_name": "target",
                "permissions": (
                    ("view_target", "View Target"),
                    ("add_target", "Add Target"),
                    ("change_target", "Change Target"),
                    ("delete_target", "Delete Target"),
                ),
            },
            bases=("tom_targets.basetarget",),
        ),
    ]
