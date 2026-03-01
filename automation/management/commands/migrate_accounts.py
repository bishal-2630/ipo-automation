import json
import os
from django.core.management.base import BaseCommand
from automation.models import Account

class Command(BaseCommand):
    help = 'Migrates accounts from accounts.json to the database'

    def handle(self, *args, **options):
        file_path = 'accounts.json'
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File {file_path} not found'))
            return

        with open(file_path, 'r') as f:
            accounts = json.load(f)

        for acc in accounts:
            account, created = Account.objects.update_or_create(
                meroshare_user=acc.get('MEROSHARE_USER'),
                defaults={
                    'meroshare_pass': acc.get('MEROSHARE_PASS'),
                    'dp_name': acc.get('DP_NAME'),
                    'crn': acc.get('CRN'),
                    'tpin': acc.get('TPIN'),
                    'bank_name': acc.get('BANK_NAME'),
                    'kitta': int(acc.get('KITTA', 10)),
                    'email': acc.get('EMAIL'),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created account: {account.meroshare_user}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated account: {account.meroshare_user}'))
