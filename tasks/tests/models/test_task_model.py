"""Unit tests for the Task model."""
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from datetime import date, timedelta
from django.test import TestCase
from ...models import Task, User, Assigned, Team_New

from django.test import TestCase
from django.utils import timezone
from .models import New_Task

class NewTaskTestCase(TestCase):
    def setUp(self):
        self.task_data = {
            "title": "Test Task",
            "information": "This is a test task.",
            "dueDate": timezone.now(),
            "priority": "High",
            "status": "Not Started",
        }

    def test_create_new_task(self):
        task = New_Task.objects.create(**self.task_data)
        self.assertEqual(task.title, self.task_data["title"])
        self.assertEqual(task.information, self.task_data["information"])
        self.assertEqual(task.dueDate, self.task_data["dueDate"])
        self.assertEqual(task.priority, self.task_data["priority"])
        self.assertEqual(task.status, self.task_data["status"])

    def test_create_task_with_duplicate_title(self):
        New_Task.objects.create(**self.task_data)
        duplicate_task_data = {
            "title": "Test Task",
            "information": "Duplicate task with the same title.",
            "dueDate": timezone.now(),
            "priority": "Medium",
            "status": "In Progress",
        }
        with self.assertRaises(Exception):
            New_Task.objects.create(**duplicate_task_data)

    def test_update_task_status(self):
        task = New_Task.objects.create(**self.task_data)
        new_status = "Completed"
        task.status = new_status
        task.save()
        updated_task = New_Task.objects.get(title=self.task_data["title"])
        self.assertEqual(updated_task.status, new_status)

    def test_default_status_value(self):
        task = New_Task.objects.create(**self.task_data)
        self.assertEqual(task.status, "Not Started")