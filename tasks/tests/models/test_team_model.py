'''Unit Tests for the Team Models'''
from django.test import TestCase
from django.http import HttpResponse
from .models import Team_New
from .views import create_team_entry, add_member, team_exists

class TeamTestCase(TestCase):
    def setUp(self):
        self.team_name = "TestTeam"
        self.user_name = "TestUser"

    def test_create_team_entry(self):
        create_team_entry(self.user_name, self.team_name)
        self.assertTrue(Team_New.objects.filter(team_name=self.team_name).exists())

    def test_create_existing_team_entry(self):
        create_team_entry(self.user_name, self.team_name)
        response = create_team_entry(self.user_name, self.team_name)
        self.assertEqual(response.content, b"Team already exists!")

    def test_add_member_to_team(self):
        create_team_entry(self.user_name, self.team_name)
        response = add_member("NewUser", self.team_name)
        self.assertEqual(response.content, b"User added to the team successfully.")

    def test_add_existing_member_to_team(self):
        create_team_entry(self.user_name, self.team_name)
        response = add_member(self.user_name, self.team_name)
        self.assertEqual(response.content, b"User already exists in the team.")

    def test_team_exists_function(self):
        self.assertTrue(team_exists(self.team_name))

    def test_team_does_not_exist_function(self):
        self.assertFalse(team_exists("NonExistentTeam"))

    def test_add_member_to_nonexistent_team(self):
        response = add_member("NewUser", "NonExistentTeam")
        self.assertEqual(response.content, b"Team does not exist.")

    def test_create_team_entry_and_check_host_status(self):
        create_team_entry(self.user_name, self.team_name)
        team = Team_New.objects.get(team_name=self.team_name)
        self.assertTrue(team.is_team_host)

    def test_create_team_entry_with_invalid_name(self):
        response = create_team_entry(self.user_name, "")
        self.assertEqual(response.content, b"Invalid team name.")