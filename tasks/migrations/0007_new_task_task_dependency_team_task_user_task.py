# Generated by Django 4.2.6 on 2023-12-10 13:15

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_task_priority_alter_task_duedate'),
    ]

    operations = [
        migrations.CreateModel(
            name='New_Task',
            fields=[
                ('title', models.CharField(max_length=100, primary_key=True, serialize=False, unique=True)),
                ('information', models.TextField(blank=True, max_length=1000)),
                ('dueDate', models.DateTimeField()),
                ('priority', models.CharField(max_length=100)),
                ('status', models.CharField(default='Not Started', max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Task_dependency',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('task_title', models.CharField(max_length=100)),
                ('dependency_task', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Team_Task',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('teamname', models.CharField(max_length=255)),
                ('task_title', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='User_Task',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=255)),
                ('task_title', models.CharField(max_length=100)),
            ],
        ),
    ]
