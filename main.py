from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import time
import pytesseract
from PIL import Image

# Load environment variables
load_dotenv()

USERNAME = os.getenv("MEROSHARE_USER")
PASSWORD = os.getenv("MEROSHARE_PASS")
DP_NAME = os.getenv("DP_NAME")
CRN = os.getenv("CRN")
TPIN = os.getenv("TPIN")
BANK_NAME = os.getenv("BANK_NAME")
KITTA = os.getenv("KITTA", "10")

# --- TESSERACT CONFIGURATION ---
# On Windows, we need to point to the exe if not in PATH.
# On Linux (GitHub Actions), 'tesseract' is usually in PATH after install.
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
        # Wait for CAPTCHA image to load
        captcha_elem = page.wait_for_selector(".captcha-image", timeout=5000)
        if not captcha_elem:
            print("⚠️ CAPTCHA image not found!")
            return None
            
        # Take screenshot of just the CAPTCHA element
        captcha_path = "captcha.png"
        captcha_elem.screenshot(path=captcha_path)
        
        # Open image with Pillow
        image = Image.open(captcha_path)
        
        # Simple preprocessing (convert to grayscale) might help accuracy
        image = image.convert('L') 
        
        # Use Tesseract to extract text
        # --psm 8 treats the image as a single word
        captcha_text = pytesseract.image_to_string(image, config='--psm 8').strip()
        
        # Clean up text (remove spaces/special chars if needed)
        captcha_text = "".join(filter(str.isalnum, captcha_text))
        
        print(f"🤖 OCR Read: '{captcha_text}'")
        return captcha_text
    except Exception as e:
        print(f"❌ OCR Error: {e}")
        return None

def login(page):
    """
    Attempts to login. Returns True if successful, False otherwise.
    Manual logic: Fills form -> Solves CAPTCHA -> Clicks Login -> Checks for Dashboard.
    """
    print(f"🔑 Logging in as {USERNAME}...")
    
    # Fill details
    page.wait_for_selector("#selectBranch")
    page.select_option("#selectBranch", label=DP_NAME)
    page.fill("#txtUserName", USERNAME)
    page.fill("#txtPassword", PASSWORD)
    
    # Solve CAPTCHA
    captcha_text = solve_captcha(page)
    if not captcha_text:
        return False
        
    # Fill CAPTCHA
    page.fill("#captchaEnter", captcha_text)
    
    # Click Login
    page.click("button:has-text('Login')")
    
    # Check if login succeeded (Dashboard element) OR failed (Error message)
    try:
        # Wait for either dashboard or error message
        # Dashboard indicator: 'My ASBA' or user profile
        # Error indicator: .toast-message or specific error text
        
        # We'll wait up to 5 seconds to see what happens
        page.wait_for_timeout(2000) 
        
        if page.locator("text=My ASBA").is_visible():
            return True
        elif page.locator(".toast-message").is_visible():
            error_msg = page.locator(".toast-message").inner_text()
            print(f"⚠️ Login Failed: {error_msg}")
            return False
        else:
            # Maybe just slow? Let's assume failure if not explicitly successful
             if page.url == "https://meroshare.cdsc.com.np/#/dashboard":
                 return True
             return False
    except Exception as e:
        print(f"⚠️ Login Check Error: {e}")
        return False

def run_automation():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            # slow_mo=50 
        )
        context = browser.new_context()
        page = context.new_page()

        print("🚀 Opening MeroShare...")
        page.goto("https://meroshare.cdsc.com.np", timeout=60000)

        # --- RETRY LOOP FOR LOGIN ---
        MAX_RETRIES = 5
        logged_in = False
        
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n🔄 Login Attempt {attempt}/{MAX_RETRIES}")
            if login(page):
                print("✅ Login Successful!")
                logged_in = True
                break
            else:
                print("❌ Login failed. Refreshing to try new CAPTCHA...")
                page.reload()
                page.wait_for_load_state('networkidle')
                time.sleep(2) # Brief pause before retry
        
        if not logged_in:
            print("❌ Max login attempts reached. Exiting.")
            browser.close()
            return

        # 2️⃣ Navigate to My ASBA
        print("📂 Navigating to My ASBA...")
        page.wait_for_selector(".nav-link:has-text('My ASBA')")
        page.click(".nav-link:has-text('My ASBA')")

        # 3️⃣ Click Apply for an IPO
        print("🔍 Looking for available IPOs...")
        page.wait_for_selector("button:has-text('Apply')")
        
        apply_buttons = page.query_selector_all("button:has-text('Apply')")
        if apply_buttons:
            print(f"✅ Found {len(apply_buttons)} IPO(s) available. Applying for the first one...")
            apply_buttons[0].click()
        else:
            print("❌ No available IPOs found to apply. Exiting.")
            browser.close()
            return

        # 4️⃣ Fill IPO form
        print("📝 Filling application form...")
        page.wait_for_selector("select[name='bank']")
        page.select_option("select[name='bank']", label=BANK_NAME)
        page.fill("input[name='appliedKitta']", KITTA)
        page.fill("input[name='crnNumber']", CRN)
        page.check("input[type='checkbox']")
        print("✅ Form filled and declaration checked.")

        # Proceed
        page.click("button:has-text('Proceed')")

        # 5️⃣ Automate TPIN
        if TPIN:
            print("🔢 Entering TPIN...")
            page.wait_for_selector("input[name='confirmationCode']")
            page.fill("input[name='confirmationCode']", TPIN)
            
            page.wait_for_timeout(1000)
            print("🚀 TPIN entered. Submitting application...")
            page.click("button:has-text('Apply')")
            print("✅ IPO application submitted automatically!")
            
            # Wait for success message visibility
            try:
                page.wait_for_selector(".toast-success", timeout=5000)
                print("✅ Success message detected!")
            except:
                pass
        else:
            print("⚠️ TPIN not found in .env. Please enter it manually and click Apply.")

        print("🏁 Automation complete.")
        page.wait_for_timeout(5000)
        browser.close()

if __name__ == "__main__":
    if not all([USERNAME, PASSWORD, DP_NAME, CRN, BANK_NAME]):
        print("❌ Missing environment variables. Please check your .env file.")
    else:
        run_automation()