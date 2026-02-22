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
        # Revert to the version that worked in Step 451
        page.wait_for_selector("[name='bank']", timeout=20000)
        page.click("[name='bank']")
        page.wait_for_timeout(1000) 
        
        page.keyboard.type(bank_name)
        page.wait_for_timeout(2000) 
        
        # Try to click highlighting or just Enter
        if page.locator(".select2-results__option--highlighted").is_visible():
            page.click(".select2-results__option--highlighted")
        else:
            page.keyboard.press("Enter")
            
        page.wait_for_timeout(1000) 

    except Exception as e:
        print(f"[{username}] Could not select bank. Capture state:")
        page.screenshot(path=f"debug_bank_results_{username}.png")
        raise e

    # Trigger validation for numeric fields
    for field in ["appliedKitta", "crnNumber"]:
        loc = page.locator(f"input[name='{field}']")
        loc.clear()
        loc.type(account.get('KITTA', '10') if field == 'appliedKitta' else account['CRN'])
        loc.dispatch_event('input')
        loc.dispatch_event('change')
        page.wait_for_timeout(500)
    
    # Checkbox jiggle
    page.uncheck("input[type='checkbox']")
    page.wait_for_timeout(500)
    page.check("input[type='checkbox']")
    page.dispatch_event("input[type='checkbox']", 'change')
    
    page.mouse.click(0, 0)
    page.wait_for_timeout(1000)
    
    print(f"Form filled. Checking Proceed button state...")
    proceed_btn = page.locator("button:has-text('Proceed')")
    is_disabled = proceed_btn.evaluate("node => node.disabled")
    
    if is_disabled:
        print(f"Warning: Proceed button is still DISABLED. Forcing it to enable...")
        # Last resort: Force enable via JS
        page.evaluate("() => { Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Proceed')).disabled = false; }")
        page.wait_for_timeout(500)

    proceed_btn.click(force=True)

    if tpin:
        print(f"[{username}] Entering TPIN...")
        page.wait_for_selector("input[name='confirmationCode']")
        page.fill("input[name='confirmationCode']", tpin)
        
        page.wait_for_timeout(1000)
        print(f"[{username}] Submitting application...")
        page.click("button:has-text('Apply')")
        
        try:
            page.wait_for_selector(".toast-success", timeout=5000)
            print(f"Application SUCCESS!")
        except:
             print(f"Warning: [{username}] Success message not detected, but submitted.")
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