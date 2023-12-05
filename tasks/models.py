from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar

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
    
class Task(models.Model):
    title = models.CharField(max_length=100)
    information = models.TextField(max_length=1000, blank=True)
    assignedUsers = models.ManyToManyField('User', through='Assigned')
    dueDate = models.DateTimeField()
    
class Assigned(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #information = models.ForeignKey(TaskInformation, on_delete=models.CASCADE)

class Team(models.Model):
    team_name = models.CharField(max_length=100, unique=True)

class TeamModel(models.Model):
    user_name = models.CharField(max_length=100)
    team = models.ManyToManyField(Team)    

def create_team(team_name):
    team_instance = Team(team_name=team_name)
    team_instance.save()
    return team_instance

def create_user(user_name, teams):
    user_instance = TeamModel(user_name=user_name)
    user_instance.save()
    user_instance.team.add(*teams)
    return user_instance

def get_users_in_team(team_name):
    return TeamModel.objects.filter(team__team_name=team_name)

def get_teams_for_user(user_name):
    try:
        user_instance = TeamModel.objects.get(user_name=user_name)
        teams_for_user = user_instance.team.all()
        return teams_for_user
    except TeamModel.DoesNotExist:
        # Handle the case where the user does not exist
        return None
    
    
    
