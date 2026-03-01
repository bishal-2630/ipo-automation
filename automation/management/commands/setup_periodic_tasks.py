from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = 'Sets up default periodic tasks for IPO automation'

    def handle(self, *args, **options):
        # Create a schedule: every day at 11:30 AM (Nepal Time is UTC+5:45)
        # 11:30 AM NPT is 05:45 AM UTC
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='45',
            hour='5',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone='UTC'
        )

        # Create the Periodic Task
        PeriodicTask.objects.get_or_create(
            crontab=schedule,
            name='Daily IPO Application Check',
            task='automation.tasks.run_all_accounts_task',
        )

        self.stdout.write(self.style.SUCCESS('Successfully configured daily automation at 11:30 AM NPT'))
        self.stdout.write(self.style.WARNING('Note: Ensure `celery -A config beat` is running along with the worker.'))
