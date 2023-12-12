from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.edit import FormView, UpdateView
from django.urls import reverse
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm, TaskForm
from tasks.forms import UpdateTaskFormInformation
from tasks.helpers import login_prohibited
from django.shortcuts import redirect
from django.http import HttpResponse
from .models import Task, Assigned, User, find_teams_by_username, create_team_entry, find_users_by_team, add_member, delete_entries_by_team_name, find_invites_by_username,find_invites_by_id, send_invite_by_username,delete_invite_by_id, delete_team_by_name_and_user
from django.db.models import Q
from tasks.forms import TaskInformationForm
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.db.models import F
from django.db.models.functions import Lower
from django.utils import timezone
from datetime import datetime, timedelta

@login_required

def dashboard(request):
    """Display the current user's dashboard."""
    
    current_user = request.user
    
    # Get all tasks related to the current user
    user_tasks = Task.objects.filter(user=current_user)

    # Sorting options
    sort_option = request.GET.get('sort', 'default')
    if sort_option == 'completed_first':
        user_tasks = user_tasks.order_by('status', 'dueDate')
    elif sort_option == 'completed_last':
        user_tasks = user_tasks.order_by('-status', 'dueDate')
    elif sort_option == 'nearest_due_date':
        user_tasks = user_tasks.order_by('dueDate')
    elif sort_option == 'farest_due_date':
        user_tasks = user_tasks.order_by('-dueDate')
    elif sort_option == 'title_AtoZ':
        user_tasks = user_tasks.order_by(Lower('title'))
    elif sort_option == 'title_ZtoA':
        user_tasks = user_tasks.order_by(Lower('-title'))
    elif sort_option == 'high_priority_first':
        user_tasks = user_tasks.order_by('priority')
    elif sort_option == 'low_priority_first':
        user_tasks = user_tasks.order_by('-priority')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        # If a search query is provided, filter tasks based on the task name
        user_tasks = user_tasks.filter(title__icontains=search_query)

    # Filter options
    filter_option = request.GET.get('filter', 'default')
    if filter_option == 'high_priority':
        user_tasks = user_tasks.filter(priority='H')
    elif filter_option == 'med_priority':
        user_tasks = user_tasks.filter(priority='M')
    elif filter_option == 'low_priority':
        user_tasks = user_tasks.filter(priority='L')
    elif filter_option == 'completed':
        user_tasks = user_tasks.filter(status='C')
    elif filter_option == 'uncompleted':
        user_tasks = user_tasks.filter(status='NC')

   
    # Limit the number of displayed tasks to 7
    limited_tasks = user_tasks[:7]

    # Filter tasks for the timeline (high priority and close due dates)
    timeline_tasks = user_tasks.filter(priority='H', dueDate__lte=datetime.now() + timedelta(days=3)).order_by('dueDate')[:3]

    return render(request, 'dashboard.html', {'user': current_user, 'tasks': limited_tasks, 'timeline_tasks': timeline_tasks, 'search_query': search_query, 'sort_option': sort_option})

def filter_timeline_tasks(tasks):
    # Filter tasks with close due date (e.g., due within the next 3 days)
    close_due_date_tasks = [task for task in tasks if task.dueDate <= datetime.now() + timedelta(days=3)]

    # Filter high priority tasks
    high_priority_tasks = [task for task in close_due_date_tasks if task.priority == 'H']

    # Sort tasks by due date
    sorted_tasks = sorted(high_priority_tasks, key=lambda task: task.dueDate)

    # Return the top 3 tasks
    return sorted_tasks[:3]


@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')

def newTask(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            Task.objects.create(
                title=form.cleaned_data.get('title'),
                information=form.cleaned_data.get('information'),
                dueDate=form.cleaned_data.get('dueDate'),
                priority=form.cleaned_data.get('priority'),  # Add this line to set the priority
            )
            users = form.cleaned_data.get('usersToAssign').split(',')
            task = Task.objects.get(title=form.cleaned_data.get('title'))
            for user in users:
                Assigned.objects.create(user=User.objects.get(username=user), task=task)
            return redirect('dashboard')
    else:
        form = TaskForm()
    return render(request, 'new_task.html', {'form': form})
def viewTasks(request):
    tasks = Task.objects.all()
    return render(request, 'viewTasks.html', {'tasks': tasks})

def deleteTask(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        if task_id:
            try:
                task = Task.objects.get(pk=task_id)
                task.delete()
            except Task.DoesNotExist:
                pass  # Handle the case where the task doesn't exist (optional)

    return redirect('viewTasks')

    

def assignUsers(request):
    form = TaskForm(request.POST)
    users = form.cleaned_data.get('usersToAssign').split(',')
    task = Task.objects.get(title=form.cleaned_data.get('title'))
    for user in users:
        Assigned.objects.create(user=user, task=task)

def updateTaskInformation(request):
    form = UpdateTaskFormInformation()
    return render(request, 'update_task_information.html', {'form': form})
    
class LoginProhibitedMixin:
    """Mixin that redirects when a user is logged in."""

    redirect_when_logged_in_url = None

    def dispatch(self, *args, **kwargs):
        """Redirect when logged in, or dispatch as normal otherwise."""
        if self.request.user.is_authenticated:
            return self.handle_already_logged_in(*args, **kwargs)
        return super().dispatch(*args, **kwargs)

    def handle_already_logged_in(self, *args, **kwargs):
        url = self.get_redirect_when_logged_in_url()
        return redirect(url)

    def get_redirect_when_logged_in_url(self):
        """Returns the url to redirect to when not logged in."""
        if self.redirect_when_logged_in_url is None:
            raise ImproperlyConfigured(
                "LoginProhibitedMixin requires either a value for "
                "'redirect_when_logged_in_url', or an implementation for "
                "'get_redirect_when_logged_in_url()'."
            )
        else:
            return self.redirect_when_logged_in_url


class LogInView(LoginProhibitedMixin, View):
    """Display login screen and handle user login."""

    http_method_names = ['get', 'post']
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def get(self, request):
        """Display log in template."""

        self.next = request.GET.get('next') or ''
        return self.render()

    def post(self, request):
        """Handle log in attempt."""

        form = LogInForm(request.POST)
        self.next = request.POST.get('next') or settings.REDIRECT_URL_WHEN_LOGGED_IN
        user = form.get_user()
        if user is not None:
            login(request, user)
            return redirect(self.next)
        messages.add_message(request, messages.ERROR, "The credentials provided were invalid!")
        return self.render()

    def render(self):
        """Render log in template with blank log in form."""

        form = LogInForm()
        return render(self.request, 'log_in.html', {'form': form, 'next': self.next})


def log_out(request):
    """Log out the current user"""

    logout(request)
    return redirect('home')


class PasswordView(LoginRequiredMixin, FormView):
    """Display password change screen and handle password change requests."""

    template_name = 'password.html'
    form_class = PasswordForm

    def get_form_kwargs(self, **kwargs):
        """Pass the current user to the password change form."""

        kwargs = super().get_form_kwargs(**kwargs)
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        """Handle valid form by saving the new password."""

        form.save()
        login(self.request, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect the user after successful password change."""

        messages.add_message(self.request, messages.SUCCESS, "Password updated!")
        return reverse('dashboard')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Display user profile editing screen, and handle profile modifications."""

    model = UserForm
    template_name = "profile.html"
    form_class = UserForm

    def get_object(self):
        """Return the object (user) to be updated."""
        user = self.request.user
        return user

    def get_success_url(self):
        """Return redirect URL after successful update."""
        messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)


class SignUpView(LoginProhibitedMixin, FormView):
    """Display the sign up screen and handle sign ups."""

    form_class = SignUpForm
    template_name = "sign_up.html"
    redirect_when_logged_in_url = settings.REDIRECT_URL_WHEN_LOGGED_IN

    def form_valid(self, form):
        self.object = form.save()
        login(self.request, self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)

def taskManagement(request):
    """Display the task management page."""

    current_user = request.user
    return render(request, 'task_management.html', {'user': current_user})

def team(request):
    """Display the team page."""

    username_param = request.GET.get('username', None)

    teams_for_user = find_teams_by_username(username_param)
    return render(request, 'team.html', {'user': username_param, 'teams': teams_for_user})

def new_team(request):
    """Display the new team page."""

    username_param = request.GET.get('username', None)
    return render(request, 'new_team.html', {'user': username_param})

def new_team_member(request):
    """Display the new team member page."""

    team_name = request.GET.get('team', None)
    username = request.GET.get('username', None)
    return render(request, 'new_team_member.html', {'teamname': team_name,'initial_user':username})

def create_new_team(request):
    username = request.GET.get('username', None)
    teamname = request.GET.get('teamname', None)

    # Create a new team entry or show a message if it already exists
    response = create_team_entry(user_name=username, team_name=teamname)
    if response:
        # If response is not None, it means the team already exists
        return response
    redirect_url = f'/team/?username={username}'
    return redirect(redirect_url)

def send_invite(request):
    username = request.GET.get('username', None)
    teamname = request.GET.get('teamname', None)
    initial_user = request.GET.get('initial_user', None)
    response =   send_invite_by_username(user_name=username,team_name=teamname, initial_user=initial_user)
    if response:
        return response
    redirect_url = f'/team/?username={initial_user}'
    return redirect(redirect_url)

def view_team_member(request):
    """Display the team member page."""

    team_name = request.GET.get('team', None)
    users = find_users_by_team(team_name=team_name)
    return render(request, 'view_team_member.html', {'users': users})

def delete_team(request):
    username = request.GET.get('username', None)
    teamname = request.GET.get('team', None)
    delete_entries_by_team_name(team_name=teamname)
    teams_for_user = find_teams_by_username(username)
    return render(request, 'team.html', {'user': username, 'teams': teams_for_user})

def view_invites(request):
    username = request.GET.get('username', None)
    invites = find_invites_by_username(username=username)
    return render(request, 'invites.html', {'user': username, 'invites': invites})

def accept_invite(request):
    inviteId = request.GET.get('invite_id', None)
    invite =  find_invites_by_id(inviteId)
    username = invite.username
    teamname = invite.teamname
    add_member(user_name=username , team_name=teamname)
    delete_invite_by_id(inviteId)
    redirect_url = f'/view_invites/?username={username}'
    return redirect(redirect_url)


def delete_invite(request):
    inviteId = request.GET.get('invite_id', None)
    invite =  find_invites_by_id(inviteId)
    username = invite.username
    delete_invite_by_id(inviteId)
    redirect_url = f'/view_invites/?username={username}'
    return redirect(redirect_url)

def leave_team(request):
    username = request.GET.get('username', None)
    teamname = request.GET.get('team', None)
    delete_team_by_name_and_user(team_name=teamname, username=username)
    teams_for_user = find_teams_by_username(username)
    return render(request, 'team.html', {'user': username, 'teams': teams_for_user})
    

def task_information(request, task_id):
    task = Task.objects.get(id=task_id)
    form = TaskInformationForm(initial={'information': task.information})
    return render(request, 'task_information.html', {'form': form}) 


def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        # Toggle the status when the checkbox is checked or unchecked
        task.status = 'C' if request.POST.get('status') == 'on' else 'NC'
        task.save()

    return HttpResponse()

def view_team_members(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    team_members = task.assignedUsers.all()  # Fetch the assigned users for the task
    return render(request, 'view_team_members.html', {'users': team_members})