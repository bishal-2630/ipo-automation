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
                "Account",
                f"IPO Automation - {account_obj.meroshare_user} - ⚠️ Dependencies missing. Please check server logs."
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

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                permissions=['geolocation'],
                geolocation={'latitude': 27.7172, 'longitude': 85.3240},
                viewport={'width': 1280, 'height': 720},
                extra_http_headers={ "Accept-Language": "en-US,en;q=0.9" }
            )
            page = context.new_page()
            
            try:
                # 3.1 Bank Balance Check
                from bank_checkers.bank import check_balance
                from .models import BankAccount
                
                bank_acc = BankAccount.objects.filter(linked_account=account_obj).first()
                if bank_acc:
                    print(f"[{account_obj.meroshare_user}] Checking bank balance...")
                    bank_page = context.new_page()
                    try:
                        balance = check_balance(
                            bank_code=bank_acc.bank,
                            phone_number=bank_acc.phone_number,
                            password=bank_acc.get_bank_password(),
                            page=bank_page,
                            account_id=account_obj.id
                        )
                        
                        status = "Success"
                        remark = f"Balance: Rs.{balance:.2f}" if balance is not None else "Failed to retrieve balance"
                        
                        if balance is not None and balance < 2000.0: # MIN_BALANCE
                            status = "Low Balance"
                        
                        ApplicationLog.objects.create(
                            account=account_obj,
                            company_name="Balance Check",
                            status=status,
                            remark=remark
                        )
                        print(f"[{account_obj.meroshare_user}] Bank Balance: {remark}")
                    except Exception as bank_err:
                        print(f"Error checking bank balance for {account_obj.meroshare_user}: {bank_err}")
                    finally:
                        bank_page.close()

                page.goto("https://meroshare.cdsc.com.np", timeout=60000)
                login_result = login(page, account_data['MEROSHARE_USER'], account_data['MEROSHARE_PASS'], account_data['DP_NAME'])
                
                if login_result is True:
                    success, result_detail = apply_ipo(page, account_data)
                    company_name = result_detail if success else "IPO Automation"
                    
                    ApplicationLog.objects.create(
                        account=account_obj,
                        company_name=company_name,
                        status="Success" if success else "Failed",
                        remark=f"Result: {result_detail}"
                    )
                    
                    if success:
                        send_fcm_notification(
                            account_obj.owner,
                            "Account",
                            f"{company_name} - {account_obj.meroshare_user} - 🚀 Applied successfully!"
                        )
                    else:
                        send_fcm_notification(
                            account_obj.owner,
                            "Account",
                            f"{company_name} - {account_obj.meroshare_user} - ⚠️ {result_detail}"
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
                        "Account",
                        f"IPO Automation - {account_obj.meroshare_user} - ⚠️ Login failed. Please check your credentials."
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
                    "Account",
                    f"IPO Automation - {account_obj.meroshare_user} - ❌ Automation crash occurred: {str(e)[:50]}"
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
                "Account",
                "IPO Automation - 🚨 Critical System Error occurred."
            )

@shared_task
def run_all_accounts_task():
    """
    Triggers apply_ipo_task for all active accounts.
    """
    active_accounts = Account.objects.filter(is_active=True)
    for account in active_accounts:
        apply_ipo_task.delay(account.id)
