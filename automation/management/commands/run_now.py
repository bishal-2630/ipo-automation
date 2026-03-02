from django.core.management.base import BaseCommand
from automation.tasks import run_all_accounts_task

class Command(BaseCommand):
    help = 'Triggers IPO automation task immediately for all active accounts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Triggering run_all_accounts_task...'))
        run_all_accounts_task()
        self.stdout.write(self.style.SUCCESS('Task triggered and queued.'))
