from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar
from django.http import HttpResponse
from django.utils import timezone

class User(AbstractUser):
    """Model used for user authentication, and team member related information."""

    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[RegexValidator(
            regex=r'^@\w{3,}$',
            message='Username must consist of @ followed by at least three alphanumericals'
        )]
    )
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(unique=True, blank=False)
    tasks = models.ManyToManyField('Task', through='Assigned')
    #updateInformation = models.ManyToManyField('TaskInformation', through='Assigned')

    class Meta:
        """Model options."""

        ordering = ['last_name', 'first_name']

    def full_name(self):
        """Return a string containing the user's full name."""

        return f'{self.first_name} {self.last_name}'

    def gravatar(self, size=120):
        """Return a URL to the user's gravatar."""

        gravatar_object = Gravatar(self.email)
        gravatar_url = gravatar_object.get_image(size=size, default='mp')
        return gravatar_url

    def mini_gravatar(self):
        """Return a URL to a miniature version of the user's gravatar."""
        
        return self.gravatar(size=60)

def get_user_by_username(username):
    try:
        user = User.objects.get(username=username)
        return user
    except User.DoesNotExist:
        return None
    
class Task(models.Model):
    class Priority (models.TextChoices):
        HIGH = "H"
        MEDIUM = "M"
        LOW = "L"
    title = models.CharField(max_length=100)
    information = models.TextField(max_length=1000, blank=True)
    assignedUsers = models.ManyToManyField('User', through='Assigned')
    dueDate = models.DateField()
    priority = models.CharField(
        max_length=1,
        choices=Priority.choices,
        default=Priority.MEDIUM)
    
class Assigned(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #information = models.ForeignKey(TaskInformation, on_delete=models.CASCADE)

class New_Task(models.Model):
    title = models.CharField(max_length=100, unique=True, primary_key=True)
    information = models.TextField(max_length=1000, blank=True)
    dueDate = models.DateTimeField()
    priority = models.CharField(max_length=100,blank=False)
    status = models.CharField(
        max_length=100,  # adjust the max length based on your status values
        default='Not Started'
    )

class Task_dependency(models.Model):
    id = models.AutoField(primary_key=True)
    task_title = models.CharField(max_length=100)
    dependency_task = models.CharField(max_length=100)

class User_Task(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    task_title = models.CharField(max_length=100)

class Time_Log(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    task_title = models.CharField(max_length=100)
    duration_minutes = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    

class Team_Task(models.Model):
    id = models.AutoField(primary_key=True)
    teamname = models.CharField(max_length=255)
    task_title = models.CharField(max_length=100)


class Team_New(models.Model):
    id = models.AutoField(primary_key=True)
    team_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    is_team_host = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.team_name} - {self.username}"
    
def team_exists(team_name):
    # Check if a team with the given name already exists in the database
    return Team_New.objects.filter(team_name=team_name).exists()    
    
def create_team_entry(user_name, team_name):
    if team_exists(team_name):
        return HttpResponse("Team already exists!")
    new_team = Team_New(username=user_name, team_name=team_name,is_team_host = True)
    new_team.save()

def add_member(user_name, team_name):
    if Team_New.objects.filter(username=user_name, team_name=team_name).exists():
        return HttpResponse("User already exists in the team!")

    # If the user doesn't exist, create a new entry
    new_team = Team_New(username=user_name, team_name=team_name)
    new_team.save()
    return HttpResponse("User added to the team successfully.")

def find_teams_by_username(username):
    teams = Team_New.objects.filter(username=username)
    return teams

def find_users_by_team(team_name):
    users = Team_New.objects.filter(team_name=team_name)
    return users

def delete_entries_by_team_name(team_name):
    entries_to_delete = Team_New.objects.filter(team_name=team_name)
    entries_to_delete.delete()

def delete_team_by_name_and_user(team_name, username):
    try:
        team = Team_New.objects.get(team_name=team_name, username=username)
        team.delete()
        return True
    except Team_New.DoesNotExist:
        return False

class Invites(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    teamname = models.CharField(max_length=255)
    teamhost_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.username} - {self.teamname}"
    
def create_invite(username, teamname, teamhost_name):
    # Create an Invites instance
    invite = Invites(username=username, teamname=teamname, teamhost_name=teamhost_name)

    # Save the instance to the database
    invite.save()

def find_invite_by_username_and_teamname(username, teamname):
    try:
        invite = Invites.objects.get(username=username, teamname=teamname)
        return invite
    except Invites.DoesNotExist:
        return None

def find_invites_by_username(username):
        invites = Invites.objects.filter(username=username)
        return invites

def delete_invite_by_id(invite_id):
        invite_to_delete= Invites.objects.filter(id=invite_id)
        if invite_to_delete:
         invite_to_delete.delete()

def find_invites_by_id(invite_id):
        Invite = Invites.objects.get(id = invite_id)
        return Invite

def send_invite_by_username(user_name , team_name , initial_user):
    user = get_user_by_username(user_name)

    if user is not None:
       if Team_New.objects.filter(username=user_name, team_name=team_name).exists():
        return HttpResponse("User already exists in the team!")
       else:
           # Check if an invite already exists for the given username and teamname
        existing_invite = find_invite_by_username_and_teamname(user_name, team_name)
        if existing_invite:
            return HttpResponse("Invite already exists for this user and team!")

        # If no existing invite, create a new one
        create_invite(username=user_name, teamname=team_name, teamhost_name=initial_user)
        
           
    else:
        # User does not exist, return an HTTP response
        return HttpResponse(f'User with username {user_name} does not exist', status=404)
    
def find_team_task_by_teamname(teamname):
    team_tasks = Team_Task.objects.filter(teamname = teamname)
    return team_tasks

def find_task_by_title(title):
    tasks = New_Task.objects.filter(title = title)
    return tasks

def find_user_task_by_username(username):
    user_tasks = User_Task.objects.filter(username = username)
    return user_tasks

def find_dependency_by_task_title (title):
    dependency = Task_dependency.objects.filter(task_title = title)
    return dependency

def find_assigned_members_by_title (title):
    assigned_members = User_Task.objects.filter(task_title = title)
    return assigned_members

class TimeLog(models.Model):
    username = models.CharField(max_length=255)
    task_title = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_minutes = models.IntegerField()