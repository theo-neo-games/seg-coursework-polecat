# Generated by Django 4.2.6 on 2023-12-12 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0009_user_task_duration_minutes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Time_Log',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=255)),
                ('task_title', models.CharField(max_length=100)),
                ('duration_minutes', models.IntegerField(default=0)),
            ],
        ),
        migrations.RemoveField(
            model_name='user_task',
            name='duration_minutes',
        ),
    ]