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
from .models import Task, Assigned, User

@login_required
def dashboard(request):
    """Display the current user's dashboard."""

    current_user = request.user
    return render(request, 'dashboard.html', {'user': current_user})
    
@login_required
def manage_teams(request):
    teams = Team.objects.filter(members=request.user)
    invitations = TeamMember.objects.filter(user=request.user, team__isnull=True)

    if request.method == 'POST':
        team_form = TeamCreationForm(request.POST)
        task_form = TaskCreationForm(request.POST)
        invitation_form = InvitationForm(request.POST)

        if team_form.is_valid():
            team = team_form.save()
            TeamMember.objects.create(user=request.user, team=team)
            messages.success(request, f'Team "{team.name}" created successfully!')

        elif task_form.is_valid():
            task = task_form.save()
            messages.success(request, f'Task "{task.name}" created successfully!')

        elif invitation_form.is_valid():
            team_id = invitation_form.cleaned_data['team_id']
            team = Team.objects.get(pk=team_id)

            recipient_username = invitation_form.cleaned_data['recipient_username']
            recipient = User.objects.get(username=recipient_username)

            if recipient not in team.members.all():
                TeamMember.objects.create(user=recipient, team=team)
                messages.success(request, f'Invitation sent to {recipient_username}!')

            else:
                messages.error(request, f'{recipient_username} is already a member of the team.')

        else:
            messages.error(request, 'Form submission failed. Please check your input.')

        return redirect('manage_teams')

    else:
        team_form = TeamCreationForm()
        task_form = TaskCreationForm()
        invitation_form = InvitationForm()

    return render(request, 'manage_teams.html', {
        'teams': teams,
        'invitations': invitations,
        'team_form': team_form,
        'task_form': task_form,
        'invitation_form': invitation_form,
    })

@login_required
def send_invitation(request, team_id):
    team = Team.objects.get(pk=team_id)

    if request.method == 'POST':
        invitation_form = InvitationForm(request.POST)
        if invitation_form.is_valid():
            recipient_username = invitation_form.cleaned_data['recipient_username']
            recipient = User.objects.get(username=recipient_username)

            # Check if the recipient is not already a member of the team
            if recipient not in team.members.all():
                TeamMember.objects.create(user=recipient, team=team)
                messages.success(request, f'Invitation sent to {recipient_username}!')
                return redirect('manage_teams')
            else:
                messages.error(request, f'{recipient_username} is already a member of the team.')

    else:
        invitation_form = InvitationForm()

    return render(request, 'send_invitation.html', {'invitation_form': invitation_form, 'team': team})

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
