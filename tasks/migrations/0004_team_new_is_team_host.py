# Generated by Django 4.2.6 on 2023-12-04 20:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_team_new'),
    ]

    operations = [
        migrations.AddField(
            model_name='team_new',
            name='is_team_host',
            field=models.BooleanField(default=False),
        ),
    ]