from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import time
import json
import random
import string
import secrets

from notifications import send_email_notification, send_push_notification
from bank_checkers.bank import check_balance
from expiry_handler import (
    detect_account_expiry,
    check_account_expiry_warning,
    handle_expired_account,
)
import re

# Load environment variables
load_dotenv()

MIN_BALANCE = 2000.0  # Minimum required balance to apply for IPO (Rs.)


def generate_new_password(length=12):
    """
    Generates a secure random password satisfying MeroShare requirements:
    - Uppercase, Lowercase, Number, and Special Character
    """
    alphabet = string.ascii_letters + string.digits + "@#$!%*?&"
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 1
                and any(c in "@#$!%*?&" for c in password)):
            return password

def update_local_account_password(username, new_password):
    """
    Updates the password for a specific user in the local accounts.json file.
    """
    if not os.path.exists("accounts.json"):
        return False

    try:
        with open("accounts.json", "r") as f:
            accounts = json.load(f)
        
        updated = False
        for acc in accounts:
            if acc.get("MEROSHARE_USER") == username:
                acc["MEROSHARE_PASS"] = new_password
                updated = True
        
        if updated:
            with open("accounts.json", "w") as f:
                json.dump(accounts, f, indent=4)
            print(f"Successfully updated local accounts.json for {username}")
            return True
    except Exception as e:
        print(f"Warning: Failed to update local accounts.json: {e}")
    return False

def handle_password_reset(page, account):
    """
    Handles the password change process when an expiry is detected.
    """
    username = account['MEROSHARE_USER']
    old_password = account['MEROSHARE_PASS']
    new_password = generate_new_password()
    
    print(f"[{username}] Starting automatic password reset...")
    try:
        # MeroShare change password page usually has these fields
        # Using flexible selectors in case they change
        page.wait_for_selector("input[placeholder='Old Password'], #oldPassword", timeout=10000)
        
        page.fill("input[placeholder='Old Password'], #oldPassword", old_password)
        page.fill("input[placeholder='New Password'], #newPassword", new_password)
        page.fill("input[placeholder='Confirm Password'], #confirmPassword", new_password)
        
        page.click("button:has-text('Change'), button:has-text('Update')")
        
        # Wait for toast message or redirection
        try:
            toast = page.wait_for_selector(".toast-success, .toast-message", timeout=10000)
            toast_text = toast.inner_text().strip()
            print(f"[{username}] Reset Result: {toast_text}")
            
            if "success" in toast_text.lower() or "successfully" in toast_text.lower():
                # Notify User
                msg = f"Your MeroShare password for {username} has been automatically reset because it expired.\n\nNew Password: {new_password}\n\nPlease update your GitHub secrets or local config if the automatic update failed."
                subj = f"[MeroShare] Password Reset Successful"
                send_email_notification(account.get('EMAIL'), subj, msg)
                send_push_notification(account.get('TOKENS'), subj, msg)
                
                # Update local file
                update_local_account_password(username, new_password)
                return True
            else:
                print(f"[{username}] Password reset reported failure: {toast_text}")
        except:
             # Fallback check: if we are no longer on change-password page and see dashboard
             page.wait_for_timeout(3000)
             if "change-password" not in page.url and (page.locator("text=My ASBA").is_visible() or "dashboard" in page.url):
                 print(f"[{username}] Password reset appears successful (redirected).")
                 msg = f"Your MeroShare password for {username} has been automatically reset.\n\nNew Password: {new_password}"
                 subj = f"[MeroShare] Password Reset Successful"
                 send_email_notification(account.get('EMAIL'), subj, msg)
                 send_push_notification(account.get('TOKENS'), subj, msg)
                 update_local_account_password(username, new_password)
                 return True
                 
    except Exception as e:
        print(f"[{username}] Error during password reset: {e}")
        page.screenshot(path=f"debug_reset_fail_{username}.png")
        
    return False
def fill_and_submit_form(page, account, company_name=None):
    """
    Fills the IPO application form and submits it with TPIN.
    Can be called from initial application or status check (Edit mode).
    """
    username = account['MEROSHARE_USER']
    tpin = account.get('TPIN')
    bank_name = account.get('BANK_NAME')

    print(f"[{username}] Filling application form...")
    # Wait for the form to actually be visible
    page.wait_for_timeout(2000)

    print(f"Selecting Bank: {bank_name}...")
    try:
        page.wait_for_selector("#selectBank", timeout=20000)

        # BRUTE FORCE JS SELECTION
        selected_bank = page.evaluate(f"""
            (bankName) => {{
                const select = document.querySelector('#selectBank');
                if (!select) return "NOT_FOUND";
                const options = Array.from(select.options);
                const target = bankName.toLowerCase().trim();
                const match = options.find(o => o.innerText.toLowerCase().trim().includes(target));
                if (match) {{
                    select.value = match.value;
                    select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    select.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    return match.innerText.trim();
                }}
                return "FAIL: " + options.map(o => o.innerText.trim()).join(', ');
            }}
        """, bank_name)

        if "FAIL" in selected_bank:
             raise Exception(f"Bank selection failed: {selected_bank}")
        print(f"[{username}] Selected Bank: {selected_bank}")

        page.wait_for_timeout(1500) # Wait for Branch to populate

        print(f"[{username}] Selecting Branch...")
        selected_branch = page.evaluate("""
            () => {
                const el = document.querySelector('#selectBranch');
                if (!el) return "NOT_FOUND";
                if (el.tagName === 'SELECT') {
                    const options = Array.from(el.options);
                    const validOptions = options.filter(o => !o.innerText.toLowerCase().includes('choose') && o.innerText.trim() !== '');
                    if (validOptions.length > 0) {
                        el.value = validOptions[0].value;
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        return "SELECT: " + validOptions[0].innerText.trim();
                    }
                    return "SELECT: NONE_FOUND";
                }
                if (el.tagName === 'INPUT') return "INPUT_FIELD";
                return "UNKNOWN_TAG: " + el.tagName;
            }
        """)

        if selected_branch == "INPUT_FIELD":
             page.click("#selectBranch")
             page.wait_for_timeout(500)
             page.keyboard.press("ArrowDown")
             page.wait_for_timeout(500)
             page.keyboard.press("Enter")
             print(f"[{username}] Selected Branch via keyboard interaction")
        elif "NOT_FOUND" in selected_branch or "NONE_FOUND" in selected_branch:
             print(f"[{username}] Branch selection auto-skipped: {selected_branch}")
        else:
             print(f"[{username}] {selected_branch}")

        page.wait_for_timeout(1000)

        print(f"[{username}] Selecting Bank Account Number...")
        page.wait_for_selector("#accountNumber", timeout=10000)
        account_selected = page.evaluate("""
            () => {
                const select = document.querySelector('#accountNumber');
                if (!select) return "NOT_FOUND";
                const options = Array.from(select.options);
                const validOptions = options.filter(o => o.innerText.trim() !== '' && !o.innerText.toLowerCase().includes('choose'));
                if (validOptions.length > 0) {
                    select.value = validOptions[0].value;
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                    select.dispatchEvent(new Event('input', { bubbles: true }));
                    return validOptions[0].innerText.trim();
                }
                return "NONE_FOUND";
            }
        """)
        print(f"[{username}] Selected Account: {account_selected}")

    except Exception as e:
        print(f"[{username}] Bank/Branch/Account selection failed. Diagnostics:")
        page.screenshot(path=f"debug_bank_fail_{username}.png")
        raise e

    print(f"[{username}] Filling Kitta and CRN with validation triggers...")
    detected_min_kitta = 10
    if not company_name:
        company_name = "Unknown"
        try:
            company_elem = page.locator(".company-name, .issue-name, h4.modal-title").first
            if company_elem.is_visible():
                company_name = company_elem.inner_text().strip()
                print(f"[{username}] Company (Detected): {company_name}")
        except: pass

    try:
        min_kitta_value = page.evaluate("""
            () => {
                const labels = Array.from(document.querySelectorAll('label, span, td, th, div'));
                const minLabel = labels.find(el => {
                    const text = el.innerText.toLowerCase().trim();
                    return text === 'minimum unit' || text === 'minimum quantity' || text === 'min unit' || 
                           text.includes('minimum unit:') || text.includes('minimum quantity:');
                });
                if (minLabel) {
                    let parent = minLabel.parentElement;
                    let textContent = parent.innerText;
                    let matches = textContent.match(/\\d+/g);
                    if (matches && matches.length > 0) return parseInt(matches[matches.length - 1]);
                    if (minLabel.nextElementSibling) {
                        const nextText = minLabel.nextElementSibling.innerText;
                        const matchNext = nextText.match(/\\d+/);
                        if (matchNext) return parseInt(matchNext[0]);
                    }
                }
                return null;
            }
        """)
        if min_kitta_value:
            detected_min_kitta = int(min_kitta_value)
            print(f"[{username}] Detected Minimum Kitta (on page): {detected_min_kitta}")

        if "RELIANCE" in company_name.upper() or "NIFRA" in company_name.upper():
            if detected_min_kitta < 50:
                 detected_min_kitta = max(detected_min_kitta, 50)
    except Exception as e:
        print(f"Warning: [{username}] Could not detect minimum kitta: {e}")

    user_kitta = int(account.get('KITTA', '10'))
    final_kitta = max(user_kitta, detected_min_kitta)
    if final_kitta != user_kitta:
        print(f"[{username}] Adjusting Kitta from {user_kitta} to {final_kitta} based on requirements.")

    kitta_loc = page.locator("#appliedKitta")
    kitta_loc.clear()
    kitta_loc.type(str(final_kitta))
    page.keyboard.press("Tab")
    page.wait_for_timeout(500)

    crn_loc = page.locator("#crnNumber")
    crn_loc.clear()
    crn_loc.type(account['CRN'])
    page.keyboard.press("Tab")
    page.wait_for_timeout(500)

    print(f"[{username}] Waiting for amount calculation...")
    try:
        page.wait_for_function("document.querySelector('#amount') && document.querySelector('#amount').value !== '' && document.querySelector('#amount').value !== '0'", timeout=5000)
        amount = page.locator("#amount").input_value()
        print(f"[{username}] Calculated Amount: {amount}")
    except:
        print(f"Warning: [{username}] Amount was not calculated.")

    page.uncheck("#disclaimer")
    page.wait_for_timeout(300)
    page.check("#disclaimer")
    page.mouse.click(0, 0)
    page.wait_for_timeout(1000)

    print(f"Form filled. Checking Proceed button state...")
    proceed_btn = page.locator("button:has-text('Proceed')")
    try:
        page.wait_for_function("document.querySelector('button:has-text(\"Proceed\")').disabled === false", timeout=5000)
    except: pass
    proceed_btn.click()

    if tpin:
        print(f"[{username}] Entering TPIN...")
        page.wait_for_selector("#transactionPIN", timeout=10000)
        page.locator("#transactionPIN").click()
        page.locator("#transactionPIN").clear()
        page.locator("#transactionPIN").type(tpin)
        page.keyboard.press("Tab")
        page.wait_for_timeout(1000)
        print(f"[{username}] Submitting application...")

        apply_btn = page.locator(".modal-footer button:has-text('Apply')").first
        if not apply_btn.is_visible():
            apply_btn = page.locator("button:has-text('Apply')").first
        apply_btn.click()

        try:
            toast = page.wait_for_selector(".toast-success, .toast-message", timeout=10000)
            toast_text = toast.inner_text().strip()
            print(f"[{username}] Result: {toast_text}")

            if "success" in toast_text.lower() or "successfully" in toast_text.lower():
                print(f"Application SUCCESS!")
                msg = f"{company_name} has been applied successfully."
                subj = f"[MeroShare] Success: {company_name}"
                send_email_notification(account.get('EMAIL'), subj, f"Hi {username},\n\n{msg}")
                send_push_notification(account.get('TOKENS'), subj, msg)
                return True, company_name
            else:
                error_msg = toast_text
                if "balance" in error_msg.lower() or "insufficient" in error_msg.lower():
                    msg = f"Your IPO has not been applied due to insufficient balance. Please topup amount and try again."
                    subj = f"[MeroShare] Failed: Insufficient Balance"
                    send_email_notification(account.get('EMAIL'), subj, f"Hi {username},\n\n{msg}")
                    send_push_notification(account.get('TOKENS'), subj, msg)
                else:
                    msg = f"❌ FAILED: {error_msg} - {username}"
                    subj = f"[MeroShare] Error: Application Failed"
                    send_email_notification(account.get('EMAIL'), subj, f"Hi {username},\n\n{msg}")
                    send_push_notification(account.get('TOKENS'), subj, msg)
                return False, error_msg
        except:
             if not page.is_visible("#transactionPIN"):
                 print(f"[{username}] Application submitted successfully (modal closed).")
                 return True, company_name
             else:
                 print(f"Error: [{username}] Application submission failed (modal still open).")
                 return False, "Application modal still open"
    else:
        print(f"Warning: [{username}] No TPIN provided. Skipping submission.")
        return False, "No TPIN"


def login(page, username, password, dp_name):
    """
    Attempts to login a specific user.
    """
    print(f"Logging in as {username}...")

    # Wait for the login page to fully load before interacting
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_timeout(2000)

    print(f"Selecting DP: {dp_name}...")
    dp_target = dp_name.lower().strip()

    # Since MeroShare uses an Angular wrapper around Select2 (<select2>), 
    # programmatic JS modifications bypass the Angular ngModel binding, 
    # leaving the form invalid. We MUST interact via the UI.
    try:
        # 1. Click the select2 container to open the dropdown
        page.locator(".select2-selection, .select2-selection--single").first.click(timeout=15000)
        page.wait_for_timeout(1000)
        
        # 2. Type the DP name into the search box
        search_box = page.locator(".select2-search__field, .select2-search input")
        search_box.first.fill(dp_name, timeout=5000)
        page.wait_for_timeout(1000)
        
        # 3. Press Enter to confirm (more reliable for Angular than clicking the option)
        page.keyboard.press("Enter")
        print(f"  DP selected via UI simulation.")
    except Exception as e:
        print(f"  Warning: UI DP selection failed: {e}")
        page.screenshot(path=f"debug_login_dp_{username}.png")

    page.wait_for_timeout(1000)

    try:
        # Use a more flexible selector for username (ID, Name, or Placeholder)
        username_selectors = ["#txtUserName", "input[name='username']", "input[placeholder='Username']"]
        found = False
        for selector in username_selectors:
            if page.locator(selector).is_visible():
                page.fill(selector, username)
                found = True
                break
        
        if not found:
            # If none found immediately, wait longer for the primary one
            page.wait_for_selector("#txtUserName", timeout=20000)
            page.fill("#txtUserName", username)
        
        # Small pause before password
        page.wait_for_timeout(500)
        
        # Robust password selection
        password_selectors = ["#txtPassword", "input[name='password']", "input[placeholder='Password']"]
        p_found = False
        for selector in password_selectors:
            if page.locator(selector).is_visible():
                page.fill(selector, password)
                p_found = True
                break
        
        if not p_found:
            page.wait_for_selector("#txtPassword", timeout=10000)
            page.fill("#txtPassword", password)
            
    except Exception as e:
        print(f"[{username}] Could not find form fields. State at failure:")
        page.screenshot(path=f"debug_login_fields_{username}.png")
        return False

    # Wait for Login button to become enabled before clicking
    # If Angular fails to enable it after 5s, we force it enabled.
    print(f"Clicking Login button for {username}...")
    try:
        page.wait_for_function(
            "() => { const btn = document.querySelector(\"button[type='submit'], button.sign-in, button:has-text('Login')\"); return btn && !btn.disabled; }",
            timeout=5000
        )
    except Exception:
        print(f"[{username}] ⚠️ Login button still disabled after 5s. Forcing it to enable...")
        page.evaluate("""
            () => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const btn = buttons.find(b => 
                    b.type === 'submit' || 
                    b.classList.contains('sign-in') || 
                    b.textContent.trim().toLowerCase() === 'login'
                );
                if (btn) {
                    btn.disabled = false;
                    btn.removeAttribute('disabled');
                    btn.classList.remove('disabled');
                }
            }
        """)
        
    page.click("button:has-text('Login'), button[type='submit'].sign-in", force=True)
    
    # Wait for navigation/dashboard
    try:
        page.wait_for_load_state('networkidle', timeout=15000)
        page.wait_for_timeout(2000) 
        
        # Check for Password Expiry Redirect
        if "change-password" in page.url or "changepassword" in page.url or page.locator("text=Change Password").is_visible():
            print(f"[{username}] ⚠️ Password Expired / Change required detected.")
            return "EXPIRED"

        # Check for DEMAT or MeroShare account expiry
        expiry_result = detect_account_expiry(page, username)
        if expiry_result:
            return expiry_result

        if page.locator("text=My ASBA").is_visible():
            return True
        elif page.locator(".toast-message").is_visible():
            error_msg = page.locator(".toast-message").inner_text()
            print(f"⚠️ Login Failed: {error_msg}")
            return False
        else:
             if "dashboard" in page.url or "dashboard" in page.content().lower():
                 return True
             return False
    except Exception as e:
        print(f"Warning: Login Check Error: {e}")
        return False

def apply_ipo(page, account):
    """
    Applies for IPO for a logged-in session.
    """
    username = account['MEROSHARE_USER']
    print(f"[{username}] Navigating to My ASBA...")
    page.wait_for_selector(".nav-link:has-text('My ASBA')")
    page.click(".nav-link:has-text('My ASBA')")

    try:
        page.wait_for_selector("a:has-text('Apply for Issue')", timeout=10000)
        page.click("a:has-text('Apply for Issue')")
        page.wait_for_load_state('networkidle')
    except Exception as e:
        print(f"Warning: [{username}] Could not find 'Apply for Issue' tab: {e}")

    print(f"[{username}] Waiting for IPO list to load...")
    page.wait_for_timeout(5000) # Increased wait for MeroShare's slow table

    # Try up to 2 times with a refresh in between if nothing found
    for attempt in range(2):
        clicked_ipo = page.evaluate("""
            () => {
                // Find all possible row containers
                const containers = Array.from(document.querySelectorAll('tr, .row, .list-item, .entry-list-item'));
                
                for (const row of containers) {
                    const text = row.innerText.toLowerCase();
                    // Find any clickable 'Apply' element (button or link)
                    const clickable = row.querySelector('button, a.btn, a[class*="btn"]');
                    if (!clickable) continue;
                    
                    const label = clickable.innerText.toLowerCase().trim();
                    if (!label.includes('apply')) continue;

                    // Keywords for Ordinary Shares
                    const isOrdinary = text.includes('ordinary') || text.includes('equity') || text.includes('public issue');
                    
                    // Keywords to exclude
                    const isExclude = text.includes('debenture') || 
                                      text.includes('bond') || 
                                      text.includes('mutual fund') || 
                                      text.includes('preference') ||
                                      text.includes('right') ||
                                      text.includes('promoter');
                    
                    if (isOrdinary && !isExclude) {
                        // Extract company name (first line or before the first dash)
                        const rawName = row.innerText.split(/[\\n-]/)[0].trim();
                        // Clean up if it grabbed headers
                        if (rawName.toLowerCase().includes('company') || rawName.length < 3) continue;
                        
                        clickable.click();
                        return rawName;
                    }
                }
                return null;
            }
        """)

        if clicked_ipo:
            break
        
        if attempt == 0:
            print(f"[{username}] No 'Ordinary Shares' found on first pass. Refreshing list...")
            page.reload(wait_until='networkidle')
            page.wait_for_timeout(4000)

    if clicked_ipo:
        print(f"[{username}] Targeted IPO: {clicked_ipo}")
        return fill_and_submit_form(page, account, company_name=clicked_ipo)
    else:
        print(f"[{username}] No 'Ordinary Shares' found to apply. Skipping silently.")
        page.screenshot(path=f"debug_asba_{username}.png")
        return False, "No ordinary shares found"

def get_accounts():
    """
    Retrieves accounts from environment variable (JSON), PostgreSQL database, or local file.
    """
    accounts = []

    # 1. Try Remote Database (PostgreSQL)
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print("Connecting to remote database to fetch accounts...")
        try:
            import psycopg2
            from cryptography.fernet import Fernet
            
            encryption_key = os.getenv("ENCRYPTION_KEY")
            cipher = None
            if encryption_key:
                try:
                    cipher = Fernet(encryption_key.encode())
                except Exception as e:
                    print(f"Warning: Invalid ENCRYPTION_KEY: {e}")

            def decrypt_val(token):
                if not token or not cipher:
                    return token
                try:
                    return cipher.decrypt(token.encode()).decode()
                except:
                    return token

            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            # Fetch accounts and join with auth_user to get the email
            # Also join with automation_bankaccount for balance checking
            cur.execute("""
                SELECT a.id, a.meroshare_user, a.meroshare_pass, a.boid, a.dp_name, a.crn, a.tpin, a.bank_name, a.kitta, u.email, a.owner_id,
                       b.bank as bank_code, b.phone_number, b.bank_password
                FROM automation_account a
                LEFT JOIN auth_user u ON a.owner_id = u.id
                LEFT JOIN automation_bankaccount b ON b.linked_account_id = a.id
                WHERE a.is_active = True;
            """)
            
            columns = [desc[0] for desc in cur.description]
            db_rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            
            for row in db_rows:
                # Fetch FCM Tokens for this user
                tokens = []
                if row.get('owner_id'):
                    cur.execute("SELECT token FROM automation_fcmtoken WHERE user_id = %s", (row['owner_id'],))
                    tokens = [t[0] for t in cur.fetchall()]

                accounts.append({
                    "ID": row['id'],
                    "MEROSHARE_USER": row['meroshare_user'],
                    "MEROSHARE_PASS": decrypt_val(row['meroshare_pass']),
                    "DP_NAME": row['dp_name'],
                    "CRN": row['crn'],
                    "TPIN": row['tpin'],
                    "BANK_NAME": row['bank_name'],
                    "KITTA": str(row['kitta']),
                    "EMAIL": row.get('email'),
                    "TOKENS": tokens,
                    "BOID": row.get('boid'),
                    "BANK_CODE": row.get('bank_code'),
                    "BANK_PHONE": row.get('phone_number'),
                    "BANK_PASS": decrypt_val(row.get('bank_password'))
                })
            
            cur.close()
            conn.close()
            if accounts:
                print(f"Successfully loaded {len(accounts)} active account(s) from database.")
                return accounts
        except ImportError:
            print("Warning: psycopg2 or cryptography not installed. Skipping database fetch.")
        except Exception as e:
            print(f"Warning: Failed to fetch accounts from database: {e}")

    # 2. Try environment variable (JSON)
    accounts_env = os.getenv("ACCOUNTS_JSON")
    if accounts_env:
        try:
            accounts = json.loads(accounts_env)
        except json.JSONDecodeError:
            print("Error: Error decoding ACCOUNTS_JSON environment variable.")

    if not accounts and os.path.exists("accounts.json"):
        try:
            with open("accounts.json", "r") as f:
                accounts = json.load(f)
        except json.JSONDecodeError:
            print("Error: Error decoding local accounts.json file.")

    if not accounts and os.getenv("MEROSHARE_USER"):
        accounts = [{
            "MEROSHARE_USER": os.getenv("MEROSHARE_USER"),
            "MEROSHARE_PASS": os.getenv("MEROSHARE_PASS"),
            "BOID": os.getenv("BOID"),
            "DP_NAME": os.getenv("DP_NAME"),
            "CRN": os.getenv("CRN"),
            "TPIN": os.getenv("TPIN"),
            "BANK_NAME": os.getenv("BANK_NAME"),
            "KITTA": os.getenv("KITTA", "10")
        }]

    return accounts

def check_status(page, account):
    """
    Refined Status Watchdog:
    1. Scrapes available IPO names from 'Apply for Issue'.
    2. Only checks the status for those specific names in 'Application Report'.
    """
    username = account['MEROSHARE_USER']
    print(f"[{username}] Starting targeted Status Watchdog...")

    try:
        # Step 1: Collect names of available IPOs from 'Apply for Issue'
        page.wait_for_selector(".nav-link:has-text('My ASBA')", timeout=15000)
        page.click(".nav-link:has-text('My ASBA')")
        page.wait_for_timeout(2000)

        page.wait_for_selector("a:has-text('Apply for Issue')", timeout=10000)
        page.click("a:has-text('Apply for Issue')")
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(3000)

        active_ipo_names = page.evaluate("""
            () => {
                const items = Array.from(document.querySelectorAll('.company-name, .issue-name, h4, .d-flex b, strong'));
                const names = [];
                for (const el of items) {
                    let text = el.innerText.trim();
                    if (text.length > 5) {
                        // Clean up: Take only the first part before any '-' or newline
                        // This usually captures the core "Super Khudi Hydropower Limited"
                        const cleanName = text.split(/[\\n-]/)[0].trim();
                        if (cleanName.length > 5) names.push(cleanName);
                    }
                }
                return [...new Set(names)];
            }
        """)

        if not active_ipo_names:
            print(f"[{username}] No active IPOs found in 'Apply for Issue'. Skipping status check.")
            return

        print(f"[{username}] Monitoring status for: {', '.join(active_ipo_names)}")

        # Step 2: Switch to 'Application Report'
        report_link_selector = "a:has-text('Application Report')"
        page.click(report_link_selector)

        # Robust wait for the list to load - handle 'loading' spinner
        print(f"[{username}] Waiting for Application Report to populate...")

        for attempt in range(2):
            try:
                # Wait for loading text/spinner to DISAPPEAR
                page.wait_for_selector("text=loading", state="detached", timeout=10000)
                # Then wait for actual buttons to appear
                page.wait_for_selector("button:has-text('Report'), a:has-text('Report')", timeout=15000)
                break
            except:
                if attempt == 0:
                    print(f"[{username}] ⏳ Report list still loading or empty. Proactively re-clicking...")
                    page.click(report_link_selector)
                    page.wait_for_timeout(3000)
                else:
                    print(f"[{username}] ⚠️ 'Report' buttons didn't appear after retry. Saving debug screenshot.")
                    page.screenshot(path=f"debug_timeout_report_{username}.png")
                    return

        for target_ipo in active_ipo_names:
            print(f"[{username}] Checking report for: {target_ipo}")
            try:
                # Identify and click 'Report' or 'Edit' for the specific IPO
                clicked_info = page.evaluate(f"""
                    (targetName) => {{
                        const targetLow = targetName.toLowerCase().trim();
                        const searchWords = targetLow.split(' ').filter(w => w.length > 2).slice(0, 3);
                        
                        // Look for common row containers
                        const allRows = Array.from(document.querySelectorAll('tr, .d-flex-row, .application-item, .card, div[class*="row"]'))
                                         .filter(el => el.querySelector('button, a'));
                        
                        for (const row of allRows) {{
                            const text = row.innerText.toLowerCase();
                            const hasFull = text.includes(targetLow);
                            const hasWords = searchWords.length > 0 && searchWords.every(w => text.includes(w));
                            
                            if (hasFull || hasWords) {{
                                // Find buttons inside this row
                                const btn = Array.from(row.querySelectorAll('button, a'))
                                             .find(el => {{
                                                 const t = el.innerText.trim().toLowerCase();
                                                 return t === 'report' || t === 'edit' || t.includes('view');
                                             }});
                                if (btn) {{
                                    btn.click();
                                    return {{ success: true, mode: btn.innerText.trim() }};
                                }}
                            }}
                        }}
                        return {{ success: false }};
                    }}
                """, target_ipo)

                if not clicked_info.get('success'):
                    print(f"[{username}] ⏳ {target_ipo} not found or has no available action.")
                    continue

                if clicked_info.get('mode', '').lower() == 'edit':
                    print(f"[{username}] 'Edit' mode detected from list view. Filling form...")
                    fill_and_submit_form(page, account, company_name=target_ipo)
                    page.goto("https://meroshare.cdsc.com.np/#/asba/report", wait_until='networkidle')
                    continue

                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(4000)

                # Read status from the detail page (robust extraction)
                detail_status = page.evaluate("""
                    () => {
                        const bodyText = document.body.innerText.toLowerCase();
                        const labels = Array.from(document.querySelectorAll('label, th, td, b, span, p, div'));
                        
                        const findValue = (searchText) => {
                            const label = labels.find(el => {
                                const t = el.innerText.toLowerCase().trim();
                                return t === searchText || t.startsWith(searchText + ':') || t.includes(searchText + ' ');
                            });
                            if (!label) return null;
                            
                            let val = null;
                            if (label.nextElementSibling) val = label.nextElementSibling.innerText.trim();
                            else if (label.parentElement && label.parentElement.nextElementSibling) {
                                val = label.parentElement.nextElementSibling.innerText.trim();
                            } else if (label.innerText.includes(':')) {
                                val = label.innerText.split(':')[1].trim();
                            }
                            
                            // Filter out garbage (dates, times, too short)
                            if (val && (val.toLowerCase().includes('date') || val.toLowerCase().includes('time') || val.length < 3)) return null;

                            return val;
                        };
                        
                        // Prioritize specific status fields
                        const statusKeys = ['block amount status', 'verification status', 'bank status', 'status'];
                        let statusLine = null;
                        for (const k of statusKeys) {
                            statusLine = findValue(k);
                            if (statusLine) break;
                        }
                        
                        // Fallback: Check if common status words are present in the body
                        if (!statusLine || statusLine.length < 3) {
                            if (bodyText.includes('verified') && !bodyText.includes('unverified')) statusLine = 'verified';
                            else if (bodyText.includes('rejected')) statusLine = 'rejected';
                            else if (bodyText.includes('unverified')) statusLine = 'unverified';
                        }

                        return { 
                            status: statusLine, 
                            remark: findValue('remark') || findValue('reason') 
                        };
                    }
                """)

                status_val = (detail_status.get('status') or "").lower()
                remark_val = (detail_status.get('remark') or "").lower()
                print(f"[{username}] {target_ipo} -> Status: {status_val}, Remark: {remark_val}")

                # Notification logic for final results
                if "verified" in status_val and "unverified" not in status_val:
                    print(f"[{username}] ✅ SUCCESS: {target_ipo} is Verified. (Email skipped as per configuration)")
                    # send_email_notification(account.get('EMAIL'), f"[MeroShare] Status: Verified!", f"Hi {username},\n\n{target_ipo} has been applied successfully.")
                elif "rejected" in status_val or "insufficient" in remark_val or "balance" in remark_val:
                    msg = f"Your IPO ({target_ipo}) was rejected. REMARK: {remark_val}."
                    print(f"[{username}] ❌ REJECTED: {msg}")

                    auto_reapply_enabled = os.getenv("AUTO_REAPPLY", "false").lower() == "true"
                    
                    if auto_reapply_enabled:
                        print(f"[{username}] Auto-reapply enabled. Looking for button...")
                        reapply_btn = page.locator("button:has-text('Edit'), button:has-text('Re-Apply'), button:has-text('Reapply')").first
                        if reapply_btn.is_visible():
                            print(f"[{username}] Found Reapply/Edit button. Clicking...")
                            reapply_btn.click()
                            page.wait_for_load_state('networkidle')
                            # fill_and_submit_form handles its own success/failure notifications
                            fill_and_submit_form(page, account, company_name=target_ipo)
                            page.goto("https://meroshare.cdsc.com.np/#/asba/report", wait_until='networkidle')
                            continue
                        else:
                            print(f"[{username}] No reapply button found for rejected IPO. Ending silently.")
                            # No notification sent when reapply enabled but button missing (silent end)
                    else:
                        print(f"[{username}] Auto-reapply disabled. Sending rejection notification.")
                        subj = f"[MeroShare] Status: Rejected"
                        body = f"Hi {username},\n\n{msg}\n\nTo reapply, please topup and the automation will retry in the next scheduled run."
                        send_email_notification(account.get('EMAIL'), subj, body)
                        send_push_notification(account.get('TOKENS'), subj, msg)
                else:
                    print(f"[{username}] ⏳ {target_ipo} still pending ({status_val}).")

                # Return to list
                page.go_back()
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(2000)

            except Exception as e:
                print(f"[{username}] Error checking {target_ipo}: {e}")
                page.goto("https://meroshare.cdsc.com.np/#/asba/report", wait_until='networkidle')

    except Exception as e:
        print(f"[{username}] Fatal error in check_status: {e}")


def run_automation():
    accounts = get_accounts()
    if not accounts:
        print("Error: No accounts found. Check accounts.json, ACCOUNTS_JSON secret, or .env file.")
        return

    count = len(accounts)
    print(f"Found {count} account(s) to process.")

    with sync_playwright() as p:
        headless = os.getenv("HEADLESS", "true").lower() == "true"
        browser = p.chromium.launch(headless=headless)

        for i, account in enumerate(accounts):
            username = account.get('MEROSHARE_USER')
            print(f"\n=============================================")
            print(f"Processing Account {i+1}/{count}: {username}")
            print(f"=============================================")

            page = browser.new_page()
            try:
                # 0. Bank Balance Check
                if account.get('BANK_CODE') and account.get('BANK_PHONE') and account.get('BANK_PASS'):
                    bank_page = browser.new_page()
                    try:
                        balance = check_balance(
                            bank_code=account['BANK_CODE'],
                            phone_number=account['BANK_PHONE'],
                            password=account['BANK_PASS'],
                            page=bank_page,
                        )
                    except Exception as e:
                        print(f"[{username}] Warning: Bank balance check failed: {e}")
                        balance = None
                    finally:
                        bank_page.close()

                    if balance is not None and balance < MIN_BALANCE:
                        print(f"[{username}] ⚠️ Balance Rs.{balance:.2f} < Rs.{MIN_BALANCE:.2f} — skipping IPO.")
                        subj = "⚠️ Low Bank Balance!"
                        msg = f"{username}: Rs.{balance:.2f} balance. Please top up to apply for IPO."
                        send_email_notification(account.get('EMAIL'), subj, msg)
                        send_push_notification(account.get('TOKENS'), subj, msg)
                        continue

                page.goto("https://meroshare.cdsc.com.np", timeout=60000)
                MAX_RETRIES = 3
                logged_in = False
                for attempt in range(1, MAX_RETRIES + 1):
                    login_result = login(page, username, account['MEROSHARE_PASS'], account['DP_NAME'])
                    if login_result is True:
                        print(f"Login Successful!")
                        logged_in = True
                        break
                    elif login_result == "EXPIRED":
                        if handle_password_reset(page, account):
                            print(f"[{username}] Password successfully reset and logged in.")
                            logged_in = True
                        else:
                            print(f"[{username}] Password reset failed.")
                        break # Don't retry login if expired/reset attempted
                    elif login_result in ("DEMAT_EXPIRED", "MEROSHARE_EXPIRED"):
                        handle_expired_account(account, login_result)
                        break
                    else:
                        print(f"Error: [{username}] Login failed (Attempt {attempt}). Retrying...")
                        page.reload()
                        page.wait_for_load_state('networkidle')
                        time.sleep(2)

                if logged_in:
                    check_account_expiry_warning(page, account)
                    apply_ipo(page, account)
                else:
                    print(f"Error: [{username}] Failed to login after {MAX_RETRIES} attempts.")

            except Exception as e:
                print(f"Error: [{username}] Error processing account: {e}")
            finally:
                page.close()

        browser.close()
        print("\nAll accounts processed.")


def solve_captcha_official(page, selector, reader):
    """
    Utility to capture and solve a captcha on a page.
    """
    try:
        captcha_img = page.locator(selector).first
        if not captcha_img.is_visible(timeout=5000):
            return None
        
        # Take a high-quality screenshot of the captcha
        img_path = f"temp_captcha_{int(time.time())}.png"
        captcha_img.screenshot(path=img_path)
        
        results = reader.readtext(img_path)
        # Clean up the temp file
        if os.path.exists(img_path):
            os.remove(img_path)
            
        res = ''.join([text for _, text, _ in results])
        res = re.sub(r'[^a-zA-Z0-9]', '', res)
        return res
    except Exception as e:
        print(f"Error solving captcha: {e}")
        return None

def run_status_check():
    """
    Official Result Check: Navigates to iporesult.cdsc.com.np
    Checks for each account's BOID against available companies.
    """
    try:
        import easyocr
    except ImportError:
        print("❌ Error: 'easyocr' is not installed. This mode requires 'easyocr'.")
        print("Please install it using: pip install easyocr")
        return

    accounts = get_accounts()
    if not accounts:
        print("Error: No accounts found.")
        return

    print(f"🔍 Official Status Check: Processing {len(accounts)} account(s)...")
    
    reader = easyocr.Reader(['en'], gpu=False)

    with sync_playwright() as p:
        headless = os.getenv("HEADLESS", "true").lower() == "true"
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        page = context.new_page()

        try:
            print("Navigating to https://iporesult.cdsc.com.np/...")
            page.goto('https://iporesult.cdsc.com.np/', timeout=60000, wait_until='networkidle')
            
            # 1. Solve initial Bot Protection if it exists
            if 'prevent automated spam submission' in page.content():
                print("Bot protection detected. Solving...")
                bot_captcha = solve_captcha_official(page, 'img', reader)
                if bot_captcha:
                    page.locator('input[type="text"]').first.fill(bot_captcha)
                    page.locator('input[type="submit"], button').first.click()
                    page.wait_for_timeout(3000)

            # 2. Get the list of companies
            page.wait_for_selector('ng-select', timeout=15000)
            page.click('ng-select')
            page.wait_for_timeout(1000)
            
            companies = page.evaluate("""
                () => {
                    const items = Array.from(document.querySelectorAll('.ng-option'));
                    return items.map(el => el.innerText.trim()).filter(t => t !== '');
                }
            """)
            
            if not companies:
                print("No companies found in the list.")
                browser.close()
                return

            print(f"Found {len(companies)} companies. Checking for latest results...")
            
            # We usually only want to check the top 2-3 latest companies to save time
            # or all of them if the user prefers. Let's check the first 2.
            target_companies = companies[:2] 

            for company in target_companies:
                print(f"\n--- Checking Result for: {company} ---")
                
                # Select the company
                page.click('ng-select')
                page.wait_for_timeout(500)
                page.type('input[type="text"]', company)
                page.keyboard.press('Enter')
                page.wait_for_timeout(500)

                for account in accounts:
                    username = account.get('MEROSHARE_USER')
                    boid = account.get('BOID')
                    
                    if not boid:
                        # Try to extract BOID from MeroShare if missing? 
                        # For now, we assume it's in the DB.
                        print(f"[{username}] Skipping: No BOID provided.")
                        continue

                    print(f"[{username}] Checking BOID: {boid}...")
                    
                    # Fill BOID
                    page.fill('input[name="boid"]', boid)
                    
                    # Solve Captcha
                    captcha_val = solve_captcha_official(page, 'img[id*="captcha"], .captcha-image img', reader)
                    if not captcha_val:
                        print(f"[{username}] Failed to solve captcha. Skipping.")
                        continue
                    
                    page.fill('input[id*="captcha"], input[placeholder*="Captcha"]', captcha_val)
                    
                    # Submit
                    page.click('button[type="submit"], .btn-primary')
                    page.wait_for_timeout(2000)

                    # Check Response
                    result_msg = page.locator('#result, .alert, .feedback').first
                    if result_msg.is_visible():
                        feedback = result_msg.inner_text().strip()
                        print(f"[{username}] Result: {feedback}")
                        
                        # Notification logic
                        if "Congratulations" in feedback or "Allotted" in feedback:
                            # Parse quantity if possible (e.g., "Allotted: 10")
                            qty_match = re.search(r'(\d+)', feedback)
                            qty = qty_match.group(1) if qty_match else "Unknown"
                            msg = f"🎉 ALLOTTED! You have been allotted {qty} shares of {company}."
                            subj = f"[MeroShare] Result: ALLOTTED!"
                            send_email_notification(account.get('EMAIL'), subj, msg)
                            send_push_notification(account.get('TOKENS'), subj, msg)
                        elif "Not Allotted" in feedback or "Sorry" in feedback:
                            # Only notify if it's a final rejection and not already notified?
                            # For simplicity, we'll notify once per run if not allotted.
                            msg = f"ℹ️ Result for {company}: Not Allotted."
                            subj = f"[MeroShare] Result: Not Allotted"
                            # send_email_notification(account.get('EMAIL'), subj, msg)
                            # send_push_notification(account.get('TOKENS'), subj, msg)
                    else:
                        print(f"[{username}] No feedback visible. Captcha might have been wrong.")
                        
                    # Clear for next account? Usually the page resets or we just overwrite.
                    page.locator('input[name="boid"]').clear()
                    page.locator('input[id*="captcha"], input[placeholder*="Captcha"]').clear()

        except Exception as e:
            print(f"Error during status check: {e}")
            page.screenshot(path="status_check_error.png")
        finally:
            browser.close()
    
    print("\nOfficial status check run complete.")


if __name__ == "__main__":
    # RUN_MODE=check_status → runs the status watchdog
    # RUN_MODE=apply (default) → applies for IPOs
    mode = os.getenv("RUN_MODE", "apply").lower()
    if mode == "check_status":
        run_status_check()
    else:
        run_automation()