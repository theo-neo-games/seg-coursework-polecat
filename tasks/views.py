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
from tasks.forms import LogInForm, PasswordForm, UserForm, SignUpForm
from tasks.helpers import login_prohibited
from django.shortcuts import redirect
from django.http import HttpResponse
from django.http import JsonResponse
import json
from datetime import datetime, date, timedelta
from .models import  User, find_teams_by_username, create_team_entry, find_users_by_team, add_member, delete_entries_by_team_name, find_invites_by_username,find_invites_by_id, send_invite_by_username,delete_invite_by_id, delete_team_by_name_and_user
from django.db.models import Q
from .models import New_Task, Task_dependency, Team_Task, User_Task,Time_Log, find_team_task_by_teamname, find_task_by_title,find_user_task_by_username, find_dependency_by_task_title, find_assigned_members_by_title
from django.db.models.functions import Lower
from .forms import SortForm
from django.utils import timezone

@login_required
    

def dashboard(request):
    """Display the current user's dashboard."""
    current_user = request.user
    user_tasks = find_user_task_by_username(current_user)
    all_tasks_for_user = []  # List to store all tasks corresponding to user

    # Search functionality
    all_tasks_for_user = searchFunction(request, user_tasks, all_tasks_for_user)

    # Sort functionality
    form = sortFunction(request, all_tasks_for_user)

    # Filter functionality
    filter_option = request.GET.get('filter', '')
    filtered_tasks = filterFunction(all_tasks_for_user, filter_option)
    
    # Initialize limited_tasks before the try block
    limited_tasks = []

    try:
        # Limit the number of displayed tasks to 6
        limited_tasks = filtered_tasks[:6]
    except UnboundLocalError:
        pass 

    context = {
        'user': current_user,
        'tasks': limited_tasks,
        'form': form,
        'filtered_tasks': filtered_tasks,
    }

    return render(request, 'dashboard.html', context)

@login_prohibited
def home(request):
    """Display the application's start/home screen."""

    return render(request, 'home.html')

def priority_order(priority):
    order = {'H': 0, 'M': 1, 'L': 2}
    return order.get(priority, float('inf'))  # Use float('inf') for unknown priorities

def viewTasks(request):
   current_user = request.user
   teams = find_teams_by_username(current_user)
   team_tasks = []
   if len(teams) > 0:
    team_tasks_1 = find_team_task_by_teamname(teamname=teams[0].team_name)
    team_tasks.extend(team_tasks_1)
    
   all_tasks_for_team = []  # List to store all tasks corresponding to team_tasks

   for team_task in team_tasks:
        tasks_for_team = find_task_by_title(title=team_task.task_title)
        all_tasks_for_team.extend(tasks_for_team)
   user_tasks = find_user_task_by_username(current_user)
   all_tasks_for_user = [] # List to store all tasks corresponding to user
   for user_task in user_tasks:
        tasks_for_user = find_task_by_title(title=user_task.task_title)
        all_tasks_for_user.extend(tasks_for_user)
    
   current_user = request.user
    
    # Get all tasks related to the current user
   user_tasks = find_user_task_by_username(current_user)
   all_tasks_for_user = [] # List to store all tasks corresponding to user

    # Search functionality
   all_tasks_for_user = searchFunction(request, user_tasks, all_tasks_for_user)

   #Filter functionality
   filter_option = request.GET.get('filter', '')
   filtered_tasks = filterFunction(all_tasks_for_user, filter_option)
   context = {
        'all_tasks_for_user': all_tasks_for_user,
        'all_tasks_for_team': all_tasks_for_team,
        'teams': teams,
        'username' : current_user,
        'filtered_tasks': filtered_tasks,
    }
   
   form = sortFunction(request, all_tasks_for_user)

   context.update({'form': form, 'all_tasks_for_user': all_tasks_for_user})

   return render(request, 'viewTasks.html', context)

    
def searchFunction(request, user_tasks, all_tasks_for_user):
    search_query = request.GET.get('search', '')
    if search_query:
        all_tasks_for_user = [task for task in all_tasks_for_user if search_query.lower() in task.title.lower()]
    else:
        for user_task in user_tasks:
            tasks_for_user = find_task_by_title(title=user_task.task_title)
            all_tasks_for_user.extend(tasks_for_user)
    return all_tasks_for_user

def sortFunction(request, all_tasks_for_user):
    form = SortForm(request.GET)
    sort_option = form['sort_option'].value() if form.is_valid() else 'default'
    if sort_option == 'due_date':
        all_tasks_for_user.sort(key=lambda x: x.dueDate)
    elif sort_option == 'title':
        all_tasks_for_user.sort(key=lambda x: x.title)
    elif sort_option == 'priority':
        all_tasks_for_user.sort(key=lambda x: (priority_order(x.priority), x.priority))
     
    return form

def filterFunction(all_tasks_for_user, filter_option):
    if filter_option == 'H':
        filtered_tasks = [task for task in all_tasks_for_user if task.priority == 'high']
    elif filter_option == 'M':
        filtered_tasks = [task for task in all_tasks_for_user if task.priority == 'mid']
    elif filter_option == 'L':
        filtered_tasks = [task for task in all_tasks_for_user if task.priority == 'low']
    elif filter_option == 'not_started':
        filtered_tasks = [task for task in all_tasks_for_user if task.status == 'Not Started']
    elif filter_option == 'working_on_it':
        filtered_tasks = [task for task in all_tasks_for_user if task.status == 'Working on it']
    elif filter_option == 'completed':
        filtered_tasks = [task for task in all_tasks_for_user if task.status == 'Completed']
    else:
      filtered_tasks = all_tasks_for_user

    return filtered_tasks
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

def assign_task(request):
    teamname = request.GET.get('team', None)
    users = find_users_by_team(team_name=teamname)
    tasks = find_team_task_by_teamname(teamname=teamname)
    return render(request, 'assign_task.html', {'users': users, 'teamname': teamname , 'tasks': tasks})

def create_new_task(task_name, task_info, due_date, priority):
    # Check if the task title already exists
    if New_Task.objects.filter(title=task_name).exists():
        return HttpResponse("Task with this title already exists.")

    # Create a new entry in the New_Task table
    new_task = New_Task(
        title=task_name,
        information=task_info,
        dueDate=due_date,
        priority=priority,
    )
    new_task.save()

    # Return None if the task is created successfully
    return None

def create_task_dependencies(task_name, dependencies):
    # Create entries in the Task_dependency table
    for dependency in dependencies:
            task_dependency = Task_dependency(
                task_title = task_name,
                dependency_task = dependency
            )
            task_dependency.save()

def create_team_task(teamname, task_name):
    # Create an entry in the Team_Task table
    team_task = Team_Task(
        teamname=teamname,
        task_title=task_name
    )
    team_task.save()

def create_user_tasks(assign_user, task_name):
    # Create entries in the User_Task table for assigned users
    for user in assign_user:
        user_task = User_Task(
            username=user,
            task_title=task_name
        )
        user_task.save()

def handle_task_submission(request):
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        task_info = request.POST.get('task_info')
        assign_user = request.POST.getlist('assign_user')
        dependencies = request.POST.getlist('dependencies')
        due_date_str = request.POST.get('due_date')
        priority = request.POST.get('priority')
        teamname = request.POST.get('teamname')

         # Convert due_date_str to a datetime object
        due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')

        # Check if the due date is less than the current time
        if due_date < datetime.now():
            return HttpResponse("Due date cannot be in the past. Please choose a future date.")

        # Call the functions to handle each task
        response = create_new_task(task_name, task_info, due_date, priority)
        
        # Check if there is a response, and return it
        if response:
            return response
        
        create_task_dependencies(task_name, dependencies)
        create_team_task(teamname, task_name)
        create_user_tasks(assign_user, task_name)


        return HttpResponse("Form submitted successfully!")
    else:
        # Handle GET requests or other methods as needed
        return HttpResponse("Invalid request method")
    
def view_dependencies(request):
    task_title = request.GET.get('task_title', None)
    dependencies = find_dependency_by_task_title(task_title)
    return render(request, 'view_dependencies.html', {'dependencies': dependencies, 'task_title': task_title})

def view_assigned_members(request):
    task_title = request.GET.get('task_title', None)
    assigned_members = find_assigned_members_by_title(task_title)
    return render(request, 'view_assigned_members.html', {'assigned_members': assigned_members, 'task_title': task_title})

def get_tasks_for_team(request, team_name):
    team_tasks = find_team_task_by_teamname(teamname=team_name)
    all_tasks_for_team = []

    for team_task in team_tasks:
        tasks_for_team = find_task_by_title(title=team_task.task_title)
        all_tasks_for_team.extend(tasks_for_team)

    # Convert tasks to a format suitable for JSON response
    tasks_data = [
        {
            'title': task.title,
            'status': task.status,
            'dueDate': task.dueDate,
        }
        for task in all_tasks_for_team
    ]

    return JsonResponse(tasks_data, safe=False)

def update_task_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_title = data.get('taskTitle')
        selected_status = data.get('selectedStatus')
        username = data.get('username')

        try:
            task = New_Task.objects.get(title=task_title)
            # Perform any additional checks here, e.g., user authorization

            # Check if the selected status is "Completed" and if the dependencies are completed
            if selected_status == 'Completed':
                dependencies = Task_dependency.objects.filter(task_title=task_title)
                for dependency in dependencies:
                    dependency_task = dependency.dependency_task
                    dependency_status = New_Task.objects.get(title=dependency_task).status
                    if dependency_status != 'Completed':
                        return JsonResponse({'success': False, 'error': f'Dependency task "{dependency_task}" is not completed'})

            # Update the task status
            task.status = selected_status
            task.save()

            return JsonResponse({'success': True})
        except New_Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def viewTimeLog(request, title, username):
    # Retrieve time log entries for the specified title and username
    time_logs = Time_Log.objects.filter(task_title=title, username=username)

    # Initialize or retrieve the summary report
    summary_report = calculate_summary_report(time_logs)

    if request.method == 'POST':
        # Handle the form submission to create a new time log entry
        minutes_spent = int(request.POST.get('minutes_spent', 0))
        Time_Log.objects.create(username=username, task_title=title, duration_minutes=minutes_spent)

        # Update time logs after adding the new entry
        time_logs = Time_Log.objects.filter(task_title=title, username=username)

        # Update the summary report after adding the new entry
        summary_report = calculate_summary_report(time_logs)

    return render(request, 'view_time_log.html', {'title': title, 'username': username, 'time_logs': time_logs, 'summary_report': summary_report})

def calculate_summary_report(time_logs):
    # Calculate total time spent on each date and overall total time
    summary_report = {}
    overall_total_time = 0

    for log in time_logs:
        log_date = log.timestamp.date()
        overall_total_time += log.duration_minutes

        if log_date not in summary_report:
            summary_report[log_date] = {'total_time': 0, 'logs': []}

        summary_report[log_date]['total_time'] += log.duration_minutes
        summary_report[log_date]['logs'].append({'timestamp': log.timestamp, 'duration_minutes': log.duration_minutes})

    # Include overall total time in the summary report
    summary_report['overall_total_time'] = overall_total_time

    return summary_report


