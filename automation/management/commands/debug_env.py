import os
import sys
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Diagnostic tool to inspect the remote environment'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"CWD: {os.getcwd()}"))
        self.stdout.write(self.style.SUCCESS(f"sys.path: {sys.path}"))
        
        self.stdout.write("\n--- Files in /app ---")
        try:
            files = os.listdir('/app')
            for f in files:
                self.stdout.write(f"- {f}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error listing /app: {e}"))
            
        self.stdout.write("\n--- Files in . ---")
        try:
            files = os.listdir('.')
            for f in files:
                self.stdout.write(f"- {f}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error listing .: {e}"))
