from celery import shared_task
from playwright.sync_api import sync_playwright
import os
import json
from .models import Account, ApplicationLog
from django.utils import timezone

# Import existing functions (we'll need to adapt them slightly to use DB instead of JSON)
# For now, let's create a task that runs the automation for a specific account

@shared_task
def apply_ipo_task(account_id):
    try:
        account_obj = Account.objects.get(id=account_id)
        # Adapt account_obj to the dictionary format expected by main.py functions
        account = {
            'MEROSHARE_USER': account_obj.meroshare_user,
            'MEROSHARE_PASS': account_obj.meroshare_pass,
            'DP_NAME': account_obj.dp_name,
            'CRN': account_obj.crn,
            'TPIN': account_obj.tpin,
            'BANK_NAME': account_obj.bank_name,
            'KITTA': str(account_obj.kitta),
            'EMAIL': account_obj.email
        }
        
        # We'll need to import the functions from main.py or move them here
        # For simplicity in this demo, let's assume we've refactored them into a module 'automation_logic'
        # But since main.py is in the root, we can try to import from it if we add root to path
        
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import login, apply_ipo
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto("https://meroshare.cdsc.com.np", timeout=60000)
                login_result = login(page, account['MEROSHARE_USER'], account['MEROSHARE_PASS'], account['DP_NAME'])
                
                if login_result is True:
                     # Log success?
                     apply_ipo(page, account)
                     # After application, we should ideally scrape the status and log it
                     # For now, let's just log that the task was triggered
                     ApplicationLog.objects.create(
                         account=account_obj,
                         company_name="Auto-Triggered",
                         status="Triggered",
                         remark="Automation task started successfully"
                     )
                else:
                     ApplicationLog.objects.create(
                         account=account_obj,
                         company_name="N/A",
                         status="Failed",
                         remark=f"Login failed: {login_result}"
                     )
            except Exception as e:
                ApplicationLog.objects.create(
                    account=account_obj,
                    company_name="N/A",
                    status="Error",
                    remark=str(e)
                )
            finally:
                browser.close()
                
    except Account.DoesNotExist:
        pass
    except Exception as e:
        print(f"Error in apply_ipo_task: {e}")

@shared_task
def run_all_accounts_task():
    accounts = Account.objects.filter(is_active=True)
    for account in accounts:
        apply_ipo_task.delay(account.id)
