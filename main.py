from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

USERNAME = os.getenv("MEROSHARE_USER")
PASSWORD = os.getenv("MEROSHARE_PASS")
DP_NAME = os.getenv("DP_NAME")
CRN = os.getenv("CRN")
TPIN = os.getenv("TPIN")
BANK_NAME = os.getenv("BANK_NAME")
KITTA = os.getenv("KITTA", "10")

def run_automation():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,   # Keep visible for manual CAPTCHA
            slow_mo=100       # Slightly slower for better stability
        )

        context = browser.new_context()
        page = context.new_page()

        print("🚀 Opening MeroShare...")
        page.goto("https://meroshare.cdsc.com.np", timeout=60000)

        # 1️⃣ Login
        print(f"🔑 Logging in as {USERNAME}...")
        page.wait_for_selector("#selectBranch")
        page.select_option("#selectBranch", label=DP_NAME)
        page.fill("#txtUserName", USERNAME)
        page.fill("#txtPassword", PASSWORD)

        print("⚠️ Please solve the CAPTCHA manually.")
        # Wait for either the dashboard to appear or a manual trigger
        # Here we still use the input() to give control to the user after login
        input("Press ENTER after solving CAPTCHA and clicking Login...")

        # 2️⃣ Navigate to My ASBA
        print("📂 Navigating to My ASBA...")
        page.wait_for_selector(".nav-link:has-text('My ASBA')")
        page.click(".nav-link:has-text('My ASBA')")

        # 3️⃣ Click Apply for an IPO
        print("🔍 Looking for available IPOs...")
        page.wait_for_selector("button:has-text('Apply')")
        
        # Get all apply buttons
        apply_buttons = page.query_selector_all("button:has-text('Apply')")
        if apply_buttons:
            print(f"✅ Found {len(apply_buttons)} IPO(s) available. Applying for the first one...")
            apply_buttons[0].click()
        else:
            print("❌ No available IPOs found to apply.")
            browser.close()
            return

        # 4️⃣ Fill IPO form
        print("📝 Filling application form...")
        page.wait_for_selector("select[name='bank']")
        
        # Select Bank
        page.select_option("select[name='bank']", label=BANK_NAME)
        
        # Fill Kitta and CRN
        page.fill("input[name='appliedKitta']", KITTA)
        page.fill("input[name='crnNumber']", CRN)

        
        page.check("input[type='checkbox']")
        print("✅ Form filled and declaration checked.")

        # Proceed to TPIN stage
        page.click("button:has-text('Proceed')")

        # 5️⃣ Automate TPIN
        if TPIN:
            print("🔢 Entering TPIN...")
            page.wait_for_selector("input[name='confirmationCode']")
            page.fill("input[name='confirmationCode']", TPIN)
            
            # small delay to ensure field is processed
            page.wait_for_timeout(1000)
            
            print("🚀 TPIN entered. Submitting application...")
            # The final button is also usually 'Apply' but can be identified by its position/class
            # In Meroshare, it's often a button with text 'Apply' in the footer of the TPIN modal
            page.click("button:has-text('Apply')")
            
            # Wait for success message or a few seconds to see result
            print("✅ IPO application submitted automatically!")
        else:
            print("⚠️ TPIN not found in .env. Please enter it manually and click Apply.")

        print("🏁 Automation complete.")
        page.wait_for_timeout(5000) # Give 5 seconds to see result before closing
        browser.close()

if __name__ == "__main__":
    if not all([USERNAME, PASSWORD, DP_NAME, CRN, BANK_NAME]):
        print("❌ Missing environment variables. Please check your .env file.")
    else:
        run_automation()