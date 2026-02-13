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
        print(f"⚠️ Warning: Tesseract not found at {TESSERACT_PATH}. Assuming it's in PATH.")

def solve_captcha(page):
    """
    Locates the CAPTCHA image, takes a screenshot, and uses Tesseract to read it.
    """
    try:
        captcha_elem = page.wait_for_selector(".captcha-image", timeout=5000)
        if not captcha_elem:
            print("⚠️ CAPTCHA image not found!")
            return None
        
        captcha_path = "captcha.png"
        captcha_elem.screenshot(path=captcha_path)
        
        image = Image.open(captcha_path).convert('L')
        captcha_text = pytesseract.image_to_string(image, config='--psm 8').strip()
        captcha_text = "".join(filter(str.isalnum, captcha_text))
        
        print(f"🤖 OCR Read: '{captcha_text}'")
        return captcha_text
    except Exception as e:
        print(f"❌ OCR Error: {e}")
        return None

def login(page, username, password, dp_name):
    """
    Attempts to login a specific user.
    """
    print(f"🔑 Logging in as {username}...")
    
    page.wait_for_selector("#selectBranch")
    page.select_option("#selectBranch", label=dp_name)
    page.fill("#txtUserName", username)
    page.fill("#txtPassword", password)
    
    captcha_text = solve_captcha(page)
    if not captcha_text:
        return False
        
    page.fill("#captchaEnter", captcha_text)
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
        print(f"⚠️ Login Check Error: {e}")
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

    print(f"📂 [{username}] Navigating to My ASBA...")
    page.wait_for_selector(".nav-link:has-text('My ASBA')")
    page.click(".nav-link:has-text('My ASBA')")

    print(f"🔍 [{username}] Looking for available IPOs...")
    try:
        page.wait_for_selector("button:has-text('Apply')", timeout=5000)
        apply_buttons = page.query_selector_all("button:has-text('Apply')")
    except:
        apply_buttons = []

    if not apply_buttons:
        print(f"❌ [{username}] No available IPOs found. Skipping.")
        return

    print(f"✅ [{username}] Found {len(apply_buttons)} IPO(s). Applying for the first one...")
    apply_buttons[0].click()

    print(f"📝 [{username}] Filling application form...")
    page.wait_for_selector("select[name='bank']")
    page.select_option("select[name='bank']", label=bank_name)
    page.fill("input[name='appliedKitta']", kitta)
    page.fill("input[name='crnNumber']", crn)
    page.check("input[type='checkbox']")
    print(f"✅ [{username}] Form filled.")

    page.click("button:has-text('Proceed')")

    if tpin:
        print(f"🔢 [{username}] Entering TPIN...")
        page.wait_for_selector("input[name='confirmationCode']")
        page.fill("input[name='confirmationCode']", tpin)
        
        page.wait_for_timeout(1000)
        print(f"🚀 [{username}] Submitting application...")
        page.click("button:has-text('Apply')")
        
        try:
            page.wait_for_selector(".toast-success", timeout=5000)
            print(f"✅ [{username}] Application SUCCESS!")
        except:
             print(f"⚠️ [{username}] Success message not detected, but submitted.")
    else:
        print(f"⚠️ [{username}] No TPIN provided. Skipping submission.")

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
            print("❌ Error decoding ACCOUNTS_JSON environment variable.")
    
    # 2. Check for local accounts.json file
    if os.path.exists("accounts.json"):
        try:
            with open("accounts.json", "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("❌ Error decoding local accounts.json file.")

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
        print("❌ No accounts found. Check accounts.json, ACCOUNTS_JSON secret, or .env file.")
        return

    print(f"👥 Found {len(accounts)} account(s) to process.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Default to headless for multi-account
        
        for i, account in enumerate(accounts):
            username = account.get('MEROSHARE_USER')
            print(f"\n=============================================")
            print(f"▶️ Processing Account {i+1}/{len(accounts)}: {username}")
            print(f"=============================================")

            context = browser.new_context()
            page = context.new_page()

            try:
                print("🚀 Opening MeroShare...")
                page.goto("https://meroshare.cdsc.com.np", timeout=60000)

                # Retry Loop
                MAX_RETRIES = 5
                logged_in = False
                for attempt in range(1, MAX_RETRIES + 1):
                    if login(page, username, account['MEROSHARE_PASS'], account['DP_NAME']):
                        print(f"✅ [{username}] Login Successful!")
                        logged_in = True
                        break
                    else:
                        print(f"❌ [{username}] Login failed (Attempt {attempt}). Retrying...")
                        page.reload()
                        page.wait_for_load_state('networkidle')
                        time.sleep(2)

                if logged_in:
                    apply_ipo(page, account)
                else:
                    print(f"❌ [{username}] Failed to login after {MAX_RETRIES} attempts.")

            except Exception as e:
                print(f"❌ [{username}] Error processing account: {e}")
            finally:
                page.close()
                context.close()
        
        browser.close()
        print("\n🏁 All accounts processed.")

if __name__ == "__main__":
    run_automation()