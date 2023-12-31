# Generated by Django 4.2.6 on 2023-12-14 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0012_alter_time_log_timestamp"),
    ]

    operations = [
        migrations.CreateModel(
            name="TimeLog",
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
                ("username", models.CharField(max_length=255)),
                ("task_title", models.CharField(max_length=255)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("duration_minutes", models.IntegerField()),
            ],
        ),
    ]
