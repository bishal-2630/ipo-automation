from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import time
import json
import pytesseract
from PIL import Image

# Load environment variables
load_dotenv()

# --- TESSERACT CONFIGURATION ---
if os.name == 'nt':
    TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    else:
        print(f"Warning: Tesseract not found at {TESSERACT_PATH}. Assuming it's in PATH.")

def solve_captcha(page):
    """
    Locates the CAPTCHA image, takes a screenshot, and uses Tesseract to read it.
    """
    try:
        # Increase timeout and add diagnostic screenshot
        try:
            captcha_elem = page.wait_for_selector(".captcha-image", timeout=15000)
        except Exception as e:
            print(f"Error: CAPTCHA not visible after 15s. Capturing state...")
            page.screenshot(path="debug_captcha_missing.png")
            raise e

        if not captcha_elem:
            print("Warning: CAPTCHA image element not found!")
            return None
        
        captcha_path = "captcha.png"
        captcha_elem.screenshot(path=captcha_path)
        
        image = Image.open(captcha_path).convert('L')
        captcha_text = pytesseract.image_to_string(image, config='--psm 8').strip()
        captcha_text = "".join(filter(str.isalnum, captcha_text))
        
        print(f"OCR Read: '{captcha_text}'")
        return captcha_text
    except Exception as e:
        print(f"Error: OCR Error: {e}")
        return None

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
    
    # Check if CAPTCHA is actually required/visible
    is_captcha_required = page.locator(".captcha-image").is_visible()
    
    if is_captcha_required:
        captcha_text = solve_captcha(page)
        if not captcha_text:
            return False
        page.fill("#captchaEnter", captcha_text)
    else:
        print(f"[{username}] No CAPTCHA required or visible. Proceeding...")

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
    try:
        # Wait for either buttons or a 'No Data' message
        page.wait_for_timeout(3000) 
        
        apply_buttons = page.query_selector_all("button:has-text('Apply')")
        
        # Diagnostic: Log what we see
        issue_names = page.query_selector_all(".issue-name") # common class for IPO names in table
        if issue_names:
            print(f"Visible Issues: {[el.inner_text().strip() for el in issue_names]}")
    except Exception as e:
        print(f"Warning: [{username}] Error scanning for buttons: {e}")
        apply_buttons = []

    if not apply_buttons:
        print(f"Error: [{username}] No available IPOs found. (Check debug_asba_{username}.png script captured)")
        page.screenshot(path=f"debug_asba_{username}.png")
        return

    print(f"Found {len(apply_buttons)} IPO(s). Applying for the first one...")
    apply_buttons[0].scroll_into_view_if_needed()
    apply_buttons[0].click()

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
        
    except Exception as e:
        print(f"[{username}] Bank/Branch selection failed. Diagnostics:")
        page.screenshot(path=f"debug_bank_fail_{username}.png")
        raise e

    # Use exact IDs from diagnostics for Kitta and CRN
    print(f"[{username}] Filling Kitta and CRN with validation triggers...")
    
    # Kitta
    kitta_loc = page.locator("#appliedKitta")
    kitta_loc.clear()
    kitta_loc.type(account.get('KITTA', '10'))
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
    is_disabled = proceed_btn.evaluate("node => node.disabled")
    
    if is_disabled:
        print(f"Warning: Proceed button is still DISABLED. Form diagnostics:")
        # One last attempt: click Kitta and press Enter
        page.click("#appliedKitta")
        page.keyboard.press("Enter")
        page.wait_for_timeout(500)
        is_disabled = proceed_btn.evaluate("node => node.disabled")
        
        if is_disabled:
            print(f"Forcing Proceed button to enable as last resort...")
            page.evaluate("() => { Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Proceed')).disabled = false; }")
            page.wait_for_timeout(500)

    proceed_btn.click(force=True)

    if tpin:
        print(f"[{username}] Entering TPIN...")
        # Exact ID is #transactionPIN
        page.wait_for_selector("#transactionPIN", timeout=10000)
        page.fill("#transactionPIN", tpin)
        
        page.wait_for_timeout(1000)
        page.wait_for_timeout(1000)
        print(f"[{username}] Submitting application...")
        
        # Click Apply and wait for ANY toast or navigation
        page.click("button:has-text('Apply')", force=True)
        
        # Take a screenshot immediately to see if any error message flashes
        page.wait_for_timeout(2000)
        page.screenshot(path=f"debug_after_apply_{username}.png")
        
        try:
            # Wait for any toast to appear
            toast = page.wait_for_selector(".toast-message, .alert, .toast-success, .toast-error", timeout=10000)
            toast_text = toast.inner_text().strip()
            print(f"[{username}] Server Response: {toast_text}")
            
            if "success" in toast_text.lower() or "successfully" in toast_text.lower():
                print(f"Application SUCCESS!")
            else:
                print(f"Application FAILED: {toast_text}")
        except:
             print(f"Warning: [{username}] No response toast detected. Checking for modal closure...")
             if not page.is_visible("#transactionPIN"):
                 print(f"[{username}] Modal closed. Likely SUCCESS, but not confirmed.")
             else:
                 print(f"Error: [{username}] Modal still open. Application FAILED.")
                 page.screenshot(path=f"debug_apply_fail_{username}.png")
    else:
        print(f"Warning: [{username}] No TPIN provided. Skipping submission.")

def get_accounts():
    """
    Retrieves accounts from environment variable (JSON) or local file.
    Falls back to single .env account if no list is found.
    """
    # 1. Check for ACCOUNTS_JSON env var (GitHub Secrets)
    accounts_env = os.getenv("ACCOUNTS_JSON")
    if accounts_env:
        try:
            return json.loads(accounts_env)
        except json.JSONDecodeError:
            print("Error: Error decoding ACCOUNTS_JSON environment variable.")
    
    # 2. Check for local accounts.json file
    if os.path.exists("accounts.json"):
        try:
            with open("accounts.json", "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error: Error decoding local accounts.json file.")

    # 3. Fallback to single .env account
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

def run_automation():
    accounts = get_accounts()
    if not accounts:
        print("Error: No accounts found. Check accounts.json, ACCOUNTS_JSON secret, or .env file.")
        return

    print(f"Found {len(accounts)} account(s) to process.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Default to headless for multi-account
        
        for i, account in enumerate(accounts):
            username = account.get('MEROSHARE_USER')
            print(f"\n=============================================")
            print(f"Processing Account {i+1}/{len(accounts)}: {username}")
            print(f"=============================================")

            context = browser.new_context()
            page = context.new_page()

            try:
                print("Opening MeroShare...")
                page.goto("https://meroshare.cdsc.com.np", timeout=60000)

                # Retry Loop
                MAX_RETRIES = 5
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
                context.close()
        
        browser.close()
        print("\nAll accounts processed.")

if __name__ == "__main__":
    run_automation()