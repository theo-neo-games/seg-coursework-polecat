from django.core.management.base import BaseCommand, CommandError

from tasks.models import User
from tasks.models import Team_New

import pytz
from faker import Faker
from random import randint, random, choice

user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe', 'user_tier': 2, 'team_name': 'Team Test', 'is_team_host': True},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe', 'user_tier': 0, 'team_name': 'Team Test', 'is_team_host': False},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson', 'user_tier': 0, 'team_name': 'Team Test', 'is_team_host': False},
]


class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 300
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self):
        self.faker = Faker('en_GB')
        self.currentTeamName = "Team " + self.faker.word().title()
        self.hostPicked = False

    def handle(self, *args, **options):
        self.create_users()
        self.users = User.objects.all()

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        user_count = User.objects.count()
        while  user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end='\r')
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)
        username = create_username(first_name, last_name)
        privileges = choice([0, 0, 0, 0, 0, 1, 1, 2])
        self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name, 'user_tier': privileges, 'team_name': self.currentTeamName, 'is_team_host': not self.hostPicked})
        if not self.hostPicked:
            self.hostPicked = True
        if randint(0, 10) == 0:
            self.currentTeamName = "Team " + self.faker.word().title()
            self.hostPicked = False
       
    def try_create_user(self, data):
        try:
            self.create_user(data)
        except:
            pass

    def create_user(self, data):
        User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
            is_staff=data['user_tier'] >= 1,
            is_superuser=data['user_tier'] >= 2
        )
        Team_New.objects.create(
            team_name=data['team_name'],
            username=data['username'],
            is_team_host=data['is_team_host']
        )

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'
