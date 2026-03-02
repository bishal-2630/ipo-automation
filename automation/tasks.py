from celery import shared_task
from playwright.sync_api import sync_playwright
import os
import json
from .models import Account, ApplicationLog
from .utils import send_fcm_notification
from django.utils import timezone
import sys

# Add the project root to sys.path to allow importing main.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

@shared_task
def apply_ipo_task(account_id):
    account_obj = None
    try:
        account_obj = Account.objects.get(id=account_id)
        
        # Debugging environment
        import os
        import sys
        cwd = os.getcwd()
        path = sys.path
        
        try:
            from main import login, apply_ipo
        except ImportError as e:
            # Try to add /app explicitly if not there
            if '/app' not in sys.path:
                sys.path.append('/app')
            
            # Check if main.py exists in common locations
            paths_to_check = ['/app/main.py', './main.py', os.path.join(cwd, 'main.py')]
            exists_info = {p: os.path.exists(p) for p in paths_to_check}
            
            # Log the error and environment info
            error_msg = f"ImportError: {str(e)}\nCWD: {cwd}\nPath: {path}\nExists: {exists_info}"
            print(error_msg)
            
            # Last ditch effort: load from source
            import importlib.util
            spec = None
            for p in paths_to_check:
                if os.path.exists(p):
                    spec = importlib.util.spec_from_file_location("main", p)
                    break
            
            if spec:
                main_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(main_module)
                login = main_module.login
                apply_ipo = main_module.apply_ipo
            else:
                raise ImportError(f"Could not find main.py in {paths_to_check}. {error_msg}")
        # Adapt account_obj to the dictionary format expected by main.py functions
        account = {
            'MEROSHARE_USER': account_obj.meroshare_user,
            'MEROSHARE_PASS': account_obj.meroshare_pass,
            'DP_NAME': account_obj.dp_name,
            'CRN': account_obj.crn,
            'TPIN': account_obj.tpin,
            'BANK_NAME': account_obj.bank_name,
            'KITTA': str(account_obj.kitta),
        }
        
        # Import is handled above inside the try block
        
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
                     send_fcm_notification(
                         account_obj.owner,
                         "IPO Applied Successfully!",
                         f"The IPO application for {account_obj.meroshare_user} has been triggered."
                     )
                else:
                     ApplicationLog.objects.create(
                         account=account_obj,
                         company_name="N/A",
                         status="Failed",
                         remark=f"Login failed: {login_result}"
                     )
                     send_fcm_notification(
                         account_obj.owner,
                         "IPO Application Failed",
                         f"Login failed for {account_obj.meroshare_user}. Please check your credentials."
                     )
            except Exception as e:
                ApplicationLog.objects.create(
                    account=account_obj,
                    company_name="N/A",
                    status="Error",
                    remark=str(e)
                )
                send_fcm_notification(
                    account_obj.owner,
                    "IPO Task Error",
                    f"An error occurred while processing {account_obj.meroshare_user}: {str(e)}"
                )
            finally:
                browser.close()
                
    except Account.DoesNotExist:
        pass
    except Exception as e:
        print(f"Critical error in apply_ipo_task: {e}")
        if account_obj:
            ApplicationLog.objects.create(
                account=account_obj,
                company_name="System",
                status="Critical Error",
                remark=f"Critical exception: {str(e)}"
            )

@shared_task
def run_all_accounts_task():
    accounts = Account.objects.filter(is_active=True)
    for account in accounts:
        apply_ipo_task.delay(account.id)
