from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import time
import json
import paho.mqtt.client as mqtt

# Load environment variables
load_dotenv()

def send_mqtt_notification(message, topic_suffix=None):
    """
    Sends a notification via MQTT to EMQX broker (broker.emqx.io).
    """
    broker = os.getenv("MQTT_BROKER") or "broker.emqx.io"
    port = int(os.getenv("MQTT_PORT") or 1883)
    base_topic = os.getenv("MQTT_BASE_TOPIC") or "mero_share/status"
    
    topic = f"{base_topic}/{topic_suffix}" if topic_suffix else base_topic
    
    try:
        # Use newer CallbackAPIVersion.VERSION2 for paho-mqtt
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        
        # Support for SSL (Port 8883 or 8084 requires TLS in script)
        if port in [8883, 8084]:
            client.tls_set()
            
        username = os.getenv("MQTT_USERNAME")
        password = os.getenv("MQTT_PASSWORD")
        if username and password:
            client.username_pw_set(username, password)
            
        client.connect(broker, port, 60)
        client.publish(topic, message)
        client.disconnect()
        print(f"MQTT Notification Sent to {topic}")
    except Exception as e:
        print(f"Warning: Failed to send MQTT notification: {e}")

def login(page, username, password, dp_name):
    """
    Attempts to login a specific user.
    """
    print(f"Logging in as {username}...")
    
    print(f"Selecting DP: {dp_name}...")
    page.wait_for_selector("#selectBranch", timeout=10000)
    page.click("#selectBranch")
    page.wait_for_timeout(1000) 
    page.keyboard.type(dp_name)
    page.wait_for_timeout(1000) 
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000) 
    
    # NEW: Try to blur the dropdown to ensure fields are interactable
    page.mouse.click(0, 0) 
    page.wait_for_timeout(500)

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
        # Diagnostic: List all inputs found on the page
        inputs = page.query_selector_all("input")
        input_info = []
        for el in inputs:
            i_id = el.get_attribute("id")
            i_name = el.get_attribute("name")
            i_type = el.get_attribute("type")
            input_info.append(f"id={i_id}, name={i_name}, type={i_type}")
        print(f"Found {len(inputs)} inputs: {input_info}")
        page.screenshot(path=f"debug_login_form_{username}.png")
        raise e
    
    # Note: CAPTCHA logic removed as per user request
    pass

    page.click("button:has-text('Login')")
    
    try:
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000) 
        
        if page.locator("text=My ASBA").is_visible():
            return True
        elif page.locator(".toast-message").is_visible():
            error_msg = page.locator(".toast-message").inner_text()
            print(f"⚠️ Login Failed: {error_msg}")
            return False
        else:
             if "dashboard" in page.url:
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
    crn = account['CRN']
    tpin = account['TPIN']
    bank_name = account['BANK_NAME']
    kitta = account.get('KITTA', '10')

    print(f"[{username}] Navigating to My ASBA...")
    page.wait_for_selector(".nav-link:has-text('My ASBA')")
    page.click(".nav-link:has-text('My ASBA')")
    
    # NEW: Move explicitly to 'Apply for Issue' tab
    print(f"[{username}] Clicking 'Apply for Issue' tab...")
    try:
        page.wait_for_selector("a:has-text('Apply for Issue')", timeout=10000)
        page.click("a:has-text('Apply for Issue')")
        page.wait_for_load_state('networkidle')
    except Exception as e:
        print(f"Warning: [{username}] Could not find 'Apply for Issue' tab: {e}")
        page.screenshot(path=f"debug_tab_fail_{username}.png")

    print(f"[{username}] Looking for available IPOs...")
    target_button = None
    try:
        # Wait for either buttons or a 'No Data' message
        page.wait_for_timeout(3000) 
        
        # We need to find the row that contains 'Ordinary Shares' and its corresponding 'Apply' button
        # Usually, MeroShare has a table where one column is 'Share Type'
        target_button = page.evaluate("""
            () => {
                const rows = Array.from(document.querySelectorAll('tr'));
                
                for (const row of rows) {
                    const rowText = row.innerText.toLowerCase();
                    const btn = row.querySelector('button');
                    
                    // Only proceed if the row has an Apply button
                    if (!btn || !btn.innerText.toLowerCase().includes('apply')) continue;

                    // STRICT: Must explicitly say "ordinary shares"
                    const isOrdinary = rowText.includes('ordinary shares') || rowText.includes('ordinary share');
                    
                    // STRICT: Block anything that looks like non-equity
                    const isDebenture  = rowText.includes('debenture') || rowText.includes('debentures');
                    const isBond       = rowText.includes('bond');
                    const isMutualFund = rowText.includes('mutual fund');
                    const isPreference = rowText.includes('preference share');
                    
                    if (isOrdinary && !isDebenture && !isBond && !isMutualFund && !isPreference) {
                        btn.click();
                        return "CLICKED_ORDINARY";
                    }
                }
                
                // No Ordinary Share IPO found — do NOT fall back
                return null;
            }
        """)
        
        if not target_button:
            msg = f"No 'Ordinary Shares' found or all available issues are Debentures/Mutual Funds for {username}."
            print(f"[{username}] {msg}")
            send_mqtt_notification(f"⚠️ {msg}", username)
    except Exception as e:
        print(f"Warning: [{username}] Error scanning for buttons: {e}")

    if not target_button:
        print(f"Error: [{username}] No suitable IPOs found to apply. (Check debug_asba_{username}.png)")
        page.screenshot(path=f"debug_asba_{username}.png")
        return

    print(f"[{username}] Filling application form...")
    
    # Wait for the form to actually be visible
    page.wait_for_timeout(2000) 
    
    print(f"Selecting Bank: {bank_name}...")
    try:
        page.wait_for_selector("#selectBank", timeout=20000)
        
        # BRUTE FORCE JS SELECTION: This finds the option by text and forces selection/events
        # It handles partial, case-insensitive, and stripped matching
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
        
        # BRUTE FORCE BRANCH SELECTION: Handles both SELECT and INPUT types
        print(f"[{username}] Selecting Branch...")
        selected_branch = page.evaluate("""
            () => {
                const el = document.querySelector('#selectBranch');
                if (!el) return "NOT_FOUND";
                
                // If it's a standard SELECT
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
                
                // If it's an INPUT (likely an autocomplete or facade)
                if (el.tagName === 'INPUT') {
                    // We'll return a signal to handle it via Playwright keyboard
                    return "INPUT_FIELD";
                }
                
                return "UNKNOWN_TAG: " + el.tagName;
            }
        """)
        
        if selected_branch == "INPUT_FIELD":
             # Handle input-based branch selection via keyboard
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
        
        # NEW: Handle Bank Account Number selection (identifed as 'invalid' field in diagnostics)
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

    # Use exact IDs from diagnostics for Kitta and CRN
    print(f"[{username}] Filling Kitta and CRN with validation triggers...")
    
    # NEW: Detect Minimum Kitta from the page
    detected_min_kitta = 10
    company_name = "Unknown"
    try:
        # Try to find the company name
        company_elem = page.locator(".company-name, .issue-name, h4.modal-title").first
        if company_elem.is_visible():
            company_name = company_elem.inner_text().strip()
            print(f"[{username}] Company: {company_name}")

        # Try to find Minimum Unit on the page
        # MeroShare usually has labels like 'Minimum Unit', 'Minimum quantity', or 'Min Unit'
        min_kitta_value = page.evaluate("""
            () => {
                const labels = Array.from(document.querySelectorAll('label, span, td, th, div'));
                const minLabel = labels.find(el => {
                    const text = el.innerText.toLowerCase().trim();
                    return text === 'minimum unit' || text === 'minimum quantity' || text === 'min unit' || 
                           text.includes('minimum unit:') || text.includes('minimum quantity:');
                });
                if (minLabel) {
                    // Try several strategies to find the value
                    
                    // 1. Check parent container for numbers
                    let parent = minLabel.parentElement;
                    let textContent = parent.innerText;
                    let matches = textContent.match(/\\d+/g);
                    if (matches && matches.length > 0) {
                        // Avoid picking up labels that start with numbers, look for the 'value' part
                        // Usually it's the last number in the group or the one following the label
                        return parseInt(matches[matches.length - 1]);
                    }
                    
                    // 2. Check next sibling
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
        
        # Try to find Share Price for logging
        share_price = page.evaluate("""
            () => {
                const labels = Array.from(document.querySelectorAll('label, span, td, th'));
                const priceLabel = labels.find(el => el.innerText.toLowerCase().includes('share price'));
                if (priceLabel) {
                    const parentText = priceLabel.parentElement.innerText;
                    const match = parentText.match(/\\d+(\\.\\d+)?/);
                    if (match) return match[0];
                }
                return null;
            }
        """)
        if share_price:
            print(f"[{username}] Share Price: {share_price}")

        # Special handling for known high-kitta companies if detection fails or for extra safety
        if "RELIANCE" in company_name.upper() or "NIFRA" in company_name.upper():
            if detected_min_kitta < 50:
                 print(f"[{username}] Special case: {company_name} detected. Ensuring at least 50 kitta.")
                 detected_min_kitta = max(detected_min_kitta, 50)

    except Exception as e:
        print(f"Warning: [{username}] Could not detect minimum kitta: {e}")

    # Determine final kitta to apply
    user_kitta = int(account.get('KITTA', '10'))
    final_kitta = max(user_kitta, detected_min_kitta)
    
    if final_kitta != user_kitta:
        print(f"[{username}] Adjusting Kitta from {user_kitta} to {final_kitta} based on requirements.")

    # Kitta
    kitta_loc = page.locator("#appliedKitta")
    kitta_loc.clear()
    kitta_loc.type(str(final_kitta))
    page.keyboard.press("Tab") # Trigger calculation
    page.wait_for_timeout(500)
    
    # CRN
    crn_loc = page.locator("#crnNumber")
    crn_loc.clear()
    crn_loc.type(account['CRN'])
    page.keyboard.press("Tab") # Trigger potential field-level validation
    page.wait_for_timeout(500)

    # NEW: Wait for Amount to populate (it should be non-empty and non-zero)
    print(f"[{username}] Waiting for amount calculation...")
    try:
        # Give it a few seconds to calculate
        page.wait_for_function("document.querySelector('#amount') && document.querySelector('#amount').value !== '' && document.querySelector('#amount').value !== '0'", timeout=5000)
        amount = page.locator("#amount").input_value()
        print(f"[{username}] Calculated Amount: {amount}")
    except:
        print(f"Warning: [{username}] Amount was not calculated. Form might be invalid.")
        # Check for visible error messages
        errors = page.locator(".text-danger").all_inner_texts()
        if errors:
            print(f"[{username}] Form Errors Found: {errors}")
    
    # Checkbox jiggle (ID is disclaimer)
    page.uncheck("#disclaimer")
    page.wait_for_timeout(300)
    page.check("#disclaimer")
    
    # Final click to blur everything
    page.mouse.click(0, 0)
    page.wait_for_timeout(1000)
    
    print(f"Form filled. Checking Proceed button state...")
    proceed_btn = page.locator("button:has-text('Proceed')")
    
    # Wait for natural enabled state if possible
    try:
        page.wait_for_function("document.querySelector('button:has-text(\"Proceed\")').disabled === false", timeout=5000)
    except:
        pass

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
        
        # Click Apply
        apply_btn = page.locator(".modal-footer button:has-text('Apply')").first
        if not apply_btn.is_visible():
            apply_btn = page.locator("button:has-text('Apply')").first
            
        apply_btn.click()
        
        try:
            # Wait for success toast
            toast = page.wait_for_selector(".toast-success, .toast-message", timeout=10000)
            toast_text = toast.inner_text().strip()
            print(f"[{username}] Result: {toast_text}")
            
            if "success" in toast_text.lower() or "successfully" in toast_text.lower():
                print(f"Application SUCCESS!")
                send_mqtt_notification(f"{company_name} has been applied successfully.", username)
            else:
                error_msg = toast_text
                print(f"Application Result: {error_msg}")
                if "balance" in error_msg.lower() or "insufficient" in error_msg.lower():
                    send_mqtt_notification(f"Your IPO has not been applied due to insufficient balance. Please topup amount and try again.", username)
                else:
                    send_mqtt_notification(f"❌ FAILED: {error_msg} - {username}", username)
        except:
             if not page.is_visible("#transactionPIN"):
                 print(f"[{username}] Application submitted successfully (modal closed).")
             else:
                 print(f"Error: [{username}] Application submission failed (modal still open).")
    else:
        print(f"Warning: [{username}] No TPIN provided. Skipping submission.")

def get_accounts():
    """
    Retrieves accounts from environment variable (JSON) or local file.
    """
    accounts_env = os.getenv("ACCOUNTS_JSON")
    if accounts_env:
        try:
            return json.loads(accounts_env)
        except json.JSONDecodeError:
            print("Error: Error decoding ACCOUNTS_JSON environment variable.")
    
    if os.path.exists("accounts.json"):
        try:
            with open("accounts.json", "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error: Error decoding local accounts.json file.")

    if os.getenv("MEROSHARE_USER"):
        return [{
            "MEROSHARE_USER": os.getenv("MEROSHARE_USER"),
            "MEROSHARE_PASS": os.getenv("MEROSHARE_PASS"),
            "DP_NAME": os.getenv("DP_NAME"),
            "CRN": os.getenv("CRN"),
            "TPIN": os.getenv("TPIN"),
            "BANK_NAME": os.getenv("BANK_NAME"),
            "KITTA": os.getenv("KITTA", "10")
        }]
    
    return []

def check_status(page, account):
    """
    Checks 'Application Report' for a final bank status.
    Sends MQTT notification ONLY when a final result (Verified/Rejected) is found.
    Stays silent if status is still 'Unverified' or 'In Process'.
    """
    username = account['MEROSHARE_USER']
    print(f"[{username}] Navigating to Application Report...")

    try:
        page.wait_for_selector(".nav-link:has-text('My ASBA')", timeout=15000)
        page.click(".nav-link:has-text('My ASBA')")
        page.wait_for_timeout(2000)

        page.wait_for_selector("a:has-text('Application Report')", timeout=10000)
        page.click("a:has-text('Application Report')")
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(3000)

        # Read the most recent application row
        result = page.evaluate("""
            () => {
                const rows = Array.from(document.querySelectorAll('table tbody tr'));
                if (!rows || rows.length === 0) return { status: 'NO_DATA', remark: '', company: '' };
                const row = rows[0];
                const cells = Array.from(row.querySelectorAll('td')).map(c => c.innerText.trim());
                return {
                    status: cells[cells.length - 2] || '',
                    remark: cells[cells.length - 1] || '',
                    company: cells[0] || 'Your IPO',
                    fullRow: row.innerText
                };
            }
        """)

        raw_status = result.get('status', '')
        raw_remark = result.get('remark', '')
        company     = result.get('company', 'Your IPO')
        status = raw_status.lower()
        remark = raw_remark.lower()

        print(f"[{username}] Status: '{raw_status}' | Remark: '{raw_remark}'")

        if 'verified' in status and 'un' not in status:
            msg = f"{company} has been applied successfully."
            print(f"[{username}] ✅ {msg}")
            send_mqtt_notification(msg, username)

        elif 'rejected' in status or 'insufficient' in remark or 'balance' in remark:
            msg = "Your IPO has not been applied due to insufficient balance. Please topup amount and try again."
            print(f"[{username}] ❌ {msg}")
            send_mqtt_notification(msg, username)

        else:
            # Still processing — wait silently for the next scheduled run
            print(f"[{username}] ⏳ Still in process ('{raw_status}'). Will re-check on next schedule run.")

    except Exception as e:
        print(f"[{username}] Error during status check: {e}")


def run_automation():
    accounts = get_accounts()
    if not accounts:
        print("Error: No accounts found. Check accounts.json, ACCOUNTS_JSON secret, or .env file.")
        return

    count = len(accounts)
    print(f"Found {count} account(s) to process.")
    send_mqtt_notification(f"🚀 IPO Automation Started: Processing {count} accounts.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for i, account in enumerate(accounts):
            username = account.get('MEROSHARE_USER')
            print(f"\n=============================================")
            print(f"Processing Account {i+1}/{count}: {username}")
            print(f"=============================================")

            page = browser.new_page()
            try:
                page.goto("https://meroshare.cdsc.com.np", timeout=60000)
                MAX_RETRIES = 3
                logged_in = False
                for attempt in range(1, MAX_RETRIES + 1):
                    if login(page, username, account['MEROSHARE_PASS'], account['DP_NAME']):
                        print(f"Login Successful!")
                        logged_in = True
                        break
                    else:
                        print(f"Error: [{username}] Login failed (Attempt {attempt}). Retrying...")
                        page.reload()
                        page.wait_for_load_state('networkidle')
                        time.sleep(2)

                if logged_in:
                    apply_ipo(page, account)
                else:
                    print(f"Error: [{username}] Failed to login after {MAX_RETRIES} attempts.")

            except Exception as e:
                print(f"Error: [{username}] Error processing account: {e}")
            finally:
                page.close()

        browser.close()
        print("\nAll accounts processed.")
        send_mqtt_notification("🏁 IPO Automation Completed for all accounts.")


def run_status_check():
    """
    Watchdog: Logs in to each account and checks Application Report.
    Only sends notification when a FINAL status is found.
    Runs silently if still in process (bank/holiday delay).
    """
    accounts = get_accounts()
    if not accounts:
        print("Error: No accounts found.")
        return

    count = len(accounts)
    print(f"🔍 Status Watchdog: Checking {count} account(s)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for i, account in enumerate(accounts):
            username = account.get('MEROSHARE_USER')
            print(f"\n=============================================")
            print(f"Status Check {i+1}/{count}: {username}")
            print(f"=============================================")

            page = browser.new_page()
            try:
                page.goto("https://meroshare.cdsc.com.np", timeout=60000)
                MAX_RETRIES = 3
                logged_in = False
                for attempt in range(1, MAX_RETRIES + 1):
                    if login(page, username, account['MEROSHARE_PASS'], account['DP_NAME']):
                        logged_in = True
                        break
                    else:
                        page.reload()
                        page.wait_for_load_state('networkidle')
                        time.sleep(2)

                if logged_in:
                    check_status(page, account)
                else:
                    print(f"Error: [{username}] Could not log in for status check.")

            except Exception as e:
                print(f"Error: [{username}] {e}")
            finally:
                page.close()

        browser.close()
        print("\nStatus check run complete.")


if __name__ == "__main__":
    # RUN_MODE=check_status → runs the status watchdog
    # RUN_MODE=apply (default) → applies for IPOs
    mode = os.getenv("RUN_MODE", "apply").lower()
    if mode == "check_status":
        run_status_check()
    else:
        run_automation()
