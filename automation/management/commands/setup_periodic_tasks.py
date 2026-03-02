from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = 'Sets up default periodic tasks for IPO automation'

    def handle(self, *args, **options):
        # 4:15 PM NPT is 10:30 AM UTC
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='30',
            hour='10',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone='UTC'
        )

        # Create or Update the Periodic Task
        PeriodicTask.objects.update_or_create(
            name='Daily IPO Application Check',
            defaults={
                'crontab': schedule,
                'task': 'automation.tasks.run_all_accounts_task',
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully configured daily automation at 11:30 AM NPT'))
        self.stdout.write(self.style.WARNING('Note: Ensure `celery -A config beat` is running along with the worker.'))
