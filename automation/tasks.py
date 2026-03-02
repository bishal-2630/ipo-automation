from celery import shared_task
import os
import sys
import json
import datetime
from django.utils import timezone
from .models import Account, ApplicationLog
from .utils import send_fcm_notification

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

@shared_task
def apply_ipo_task(account_id):
    """
    Celery task to apply for IPO. 
    In a hybrid environment, this should ideally only run on the GitHub Action runner,
    but we keep it here for compatibility and manual triggers if environment allows.
    """
    account_obj = None
    try:
        account_obj = Account.objects.get(id=account_id)
        
        # 1. Attempt deep imports (Playwright and Main logic)
        try:
            from playwright.sync_api import sync_playwright
            from main import login, apply_ipo
        except ImportError as e:
            error_msg = f"Automation dependencies (Playwright/Main) not available: {e}"
            print(error_msg)
            ApplicationLog.objects.create(
                account=account_obj,
                company_name="IPO Automation",
                status="Error",
                remark=error_msg
            )
            send_fcm_notification(
                account_obj.owner,
                "Automation Error",
                f"Dependencies missing for {account_obj.meroshare_user}. Please check server logs."
            )
            return

        # 2. Prepare data
        account_data = {
            'MEROSHARE_USER': account_obj.meroshare_user,
            'MEROSHARE_PASS': account_obj.meroshare_pass,
            'DP_NAME': account_obj.dp_name,
            'CRN': account_obj.crn,
            'TPIN': account_obj.tpin,
            'BANK_NAME': account_obj.bank_name,
            'KITTA': str(account_obj.kitta),
        }

        # 3. Execute Automation
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto("https://meroshare.cdsc.com.np", timeout=60000)
                login_result = login(page, account_data['MEROSHARE_USER'], account_data['MEROSHARE_PASS'], account_data['DP_NAME'])
                
                if login_result is True:
                    apply_ipo(page, account_data)
                    ApplicationLog.objects.create(
                        account=account_obj,
                        company_name="IPO Automation",
                        status="Success",
                        remark="IPO applied successfully via automation task"
                    )
                    send_fcm_notification(
                        account_obj.owner,
                        "🚀 IPO Applied!",
                        f"IPO application for {account_obj.meroshare_user} was successful."
                    )
                else:
                    ApplicationLog.objects.create(
                        account=account_obj,
                        company_name="IPO Automation",
                        status="Failed",
                        remark=f"Login failed: {login_result}"
                    )
                    send_fcm_notification(
                        account_obj.owner,
                        "⚠️ Application Failed",
                        f"Login failed for {account_obj.meroshare_user}. Please check your credentials."
                    )
            except Exception as e:
                ApplicationLog.objects.create(
                    account=account_obj,
                    company_name="IPO Automation",
                    status="Error",
                    remark=f"Exception during application: {str(e)}"
                )
                send_fcm_notification(
                    account_obj.owner,
                    "❌ Automation Crash",
                    f"An error occurred while applying for {account_obj.meroshare_user}."
                )
            finally:
                browser.close()

    except Exception as e:
        print(f"Critical error in apply_ipo_task: {e}")
        if account_obj:
            ApplicationLog.objects.create(
                account=account_obj,
                company_name="System",
                status="Critical Error",
                remark=f"Critical exception: {str(e)}"
            )
            send_fcm_notification(
                account_obj.owner,
                "🚨 Critical System Error",
                "A critical error occurred in the IPO automation system."
            )

@shared_task
def run_all_accounts_task():
    """
    Triggers apply_ipo_task for all active accounts.
    """
    active_accounts = Account.objects.filter(is_active=True)
    for account in active_accounts:
        apply_ipo_task.delay(account.id)
