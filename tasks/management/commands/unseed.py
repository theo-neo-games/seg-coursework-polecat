from django.core.management.base import BaseCommand, CommandError
from tasks.models import User, Team_New, New_Task, Team_Task

class Command(BaseCommand):
    """Build automation command to unseed the database."""
    
    help = 'Seeds the database with sample data'

    def handle(self, *args, **options):
        """Unseed the database."""

        User.objects.all().delete()
        Team_New.objects.all().delete()
        New_Task.objects.all().delete()
        Team_Task.objects.all().delete()