"""Unit tests for the Task model."""
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from datetime import date, timedelta
from django.test import TestCase
from ...models import Task, User, Assigned, Team_New

class TaskModelTestCase(TestCase):
    def setUp(self):
        self.task = Task.objects.create(
            title='Test Task',
            information='This is a test task.',
            dueDate=date.today(),
            status=Task.Status.NOT_COMPLETED
        )
        self.user = self.create_user()
        self.create_team_new()
        Assigned.objects.create(user = self.user, task = self.task)


    def create_team_new(self):
        team_new = Team_New.objects.create(
            username=self.user.username,
            team_name='Polecat',
            is_team_host=True
        )
        return team_new

    def create_user(self):
        user = User.objects.create_user(
            username= '@janedoe',
            first_name= 'Jane', 
            last_name= 'Doe', 
            email='janedoe@example.org', 
        )
        return user

    def create_user2(self):
        user = User.objects.create_user(
            username= '@johndoe',
            first_name= 'John', 
            last_name= 'Doe', 
            email='johndoe@example.org', 
        )
        return user

    '''def test_invalid_assignment(self):
        Assigned.objects.create(user = self.create_user2(), task = self.task)
        self.assert_invalid_task()'''

    def test_valid_task(self):
        self.assert_valid_task()

    def test_default_priority(self):
        self.assertEqual(self.task.priority, 'M')

    def test_default_status(self):
        self.assertEqual(self.task.status, 'NC')

    def test_invalid_status1(self):
        self.task.status = "NP"
        self.assert_invalid_task()   

    def test_invalid_status2(self):
        self.task.status = "NOT"
        self.assert_invalid_task() 

    def test_valid_priority(self):
        self.task.priority = "M"
        self.assert_valid_task()

    def test_invalid_priority(self):
        self.task.priority = "V"
        self.assert_invalid_task()

    def test_valid_date(self):
        self.task.dueDate = date.today() + timedelta(days=1)
        self.assert_valid_task()

    def test_invalid_date(self):
        self.task.dueDate = date.today() - timedelta(days=1)
        self.assert_invalid_task()

    def test_blank_title(self):
        self.task.title = ''
        self.assert_invalid_task()

    def test_blank_info(self):
        self.task.information = ''
        self.assert_valid_task()

    def test_100_char_title(self):
        self.task.title = 'x' * 100
        self.assert_valid_task()

    def test_101_char_title(self):
        self.task.title = 'x' * 101
        self.assert_invalid_task()

    def test_1000_char_info(self):
        self.task.information = 'x' * 1000
        self.assert_valid_task()

    def test_1001_char_info(self):
        self.task.information = 'x' * 1001
        self.assert_invalid_task()

    def assert_valid_task(self):
        try:
            self.task.full_clean()
        except (ValidationError):
            self.fail('Test user should be valid')

    def assert_invalid_task(self):
        with self.assertRaises(ValidationError):
            self.task.full_clean()