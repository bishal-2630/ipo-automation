"""
bank_checkers/bank.py
---------------------
Config-driven multi-bank balance checker for Nepali internet banking portals.
"""

from playwright.sync_api import Page
import re, time, requests, os

# -------------------------------------------------------------------
# Bank registry (Comprehensive mapping for Class A & B banks)
# -------------------------------------------------------------------
BANK_CONFIGS: dict[str, dict] = {
    # --- Commercial Banks (Class A) ---
    "nic_asia": {
        "name": "NIC Asia Bank",
        "url": "https://omni.nicasiabank.com/sign-in",
        "user_sel": "#nd-input-1, input[placeholder='Enter Mobile Number']",
        "pass_sel": "#nd-input-0, input[placeholder='Enter Password'], input[type='password']",
        "submit_sel": "button.nd-button--primary, button:has-text('Log In')",
        "balance_sel": "span.balance-amount, .available-balance, .amt-balance, .nd-balance-value, .total-balance, [class*='balance-amount']",
    },
    "nabil": {
        "name": "Nabil Bank",
        "url": "https://ebanking.nabilbank.com",
        "user_sel": "#txtLoginId",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit'], input[value='Login']",
        "balance_sel": "[class*='balance']",
    },
    "laxmi_sunrise": {
        "name": "Laxmi Sunrise Bank",
        "url": "https://ebanking.laxmibank.com.np",
        "user_sel": "#UserID",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "global_ime": {
        "name": "Global IME Bank",
        "url": "https://ebanking.globalimebank.com",
        "user_sel": "#txtUserName",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": "[class*='balance']",
    },
    "himalayan": {
        "name": "Himalayan Bank",
        "url": "https://ebanking.himalayanbank.com",
        "user_sel": "input[name='username']",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "nmb": {
        "name": "NMB Bank",
        "url": "https://ebanking.nmb.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "prabhu": {
        "name": "Prabhu Bank",
        "url": "https://ebanking.prabhubank.com",
        "user_sel": "input[name='username']",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "siddhartha": {
        "name": "Siddhartha Bank",
        "url": "https://ebanking.siddharthabank.com",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "sanima": {
        "name": "Sanima Bank",
        "url": "https://ebanking.sanimabank.com",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "kumari": {
        "name": "Kumari Bank",
        "url": "https://ebanking.kumaribank.com",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "machhapuchchhre": {
        "name": "Machhapuchchhre Bank",
        "url": "https://ebanking.machbank.com",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "everest": {
        "name": "Everest Bank",
        "url": "https://omni.ebl-zone.com/log-in/identify",
        "user_sel": "input[placeholder*='Mobile']",
        "proceed_sel": "button:has-text('Proceed')",
        "pass_sel": "input[type='password']",
        "submit_sel": "button:has-text('Login'), button:has-text('Sign In')",
        "balance_sel": "[class*='balance'], .balance",
    },
    "sbi": {
        "name": "Nepal SBI Bank",
        "url": "https://ebanking.nepalsbi.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "scb": {
        "name": "Standard Chartered Bank",
        "url": "https://retail.sc.com/np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "prime": {
        "name": "Prime Commercial Bank",
        "url": "https://ebanking.primebank.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "agriculture": {
        "name": "Agriculture Development Bank",
        "url": "https://ebanking.adbl.gov.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "rbb": {
        "name": "Rastriya Banijya Bank",
        "url": "https://ebanking.rbb.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "nepal_bank": {
        "name": "Nepal Bank",
        "url": "https://ebanking.nepalbank.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "nimb": {
        "name": "Nepal Investment Mega Bank",
        "url": "https://ebanking.nimb.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "citizens": {
        "name": "Citizens Bank International",
        "url": "https://ebanking.citizensbank.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },

    # --- National Level Development Banks (Class B) ---
    "garima": {
        "name": "Garima Bikas Bank",
        "url": "https://ebanking.garimabikas.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "muktinath": {
        "name": "Muktinath Bikas Bank",
        "url": "https://ebanking.mumbank.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "jyoti": {
        "name": "Jyoti Bikas Bank",
        "url": "https://ebanking.jyotibikasbank.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "kamana": {
        "name": "Kamana Sewa Bikas Bank",
        "url": "https://ebanking.kamanasewabank.com",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "lumbini": {
        "name": "Lumbini Bikas Bank",
        "url": "https://ebanking.lumbinibikasbank.com",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "mahalaxmi": {
        "name": "Mahalaxmi Bikas Bank",
        "url": "https://ebanking.mahalaxmibank.com",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "shangrila": {
        "name": "Shangri-la Bikas Bank",
        "url": "https://ebanking.shangrilabank.com",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
    "shine_resunga": {
        "name": "Shine Resunga Development Bank",
        "url": "https://ebanking.srdb.com.np",
        "user_sel": "#username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
    },
}

def _extract_balance(text: str) -> float | None:
    """Pull the first number that looks like a balance from a text string."""
    if not text: return None
    nums = re.findall(r'[\d,]+(?:\.\d+)?', text)
    for n in nums:
        val = float(n.replace(',', ''))
        if val > 0: return val
    return None

def _discover_login_page(bank_name: str, page: Page) -> str | None:
    """Uses a search engine (DuckDuckGo) to find the bank's internet banking login page."""
    # For NIC Asia and similar, we prefer search for 'mobile banking' or 'motank' or 'omni'
    search_query = f"{bank_name} mobile banking login portal" if "nic" in bank_name.lower() else f"{bank_name} internet banking login"
    print(f"  [Discovery] Searching for '{search_query}' via DuckDuckGo...")
    search_url = f"https://duckduckgo.com/?q={search_query.replace(' ', '+')}"
    try:
        page.goto(search_url, timeout=30000)
        page.wait_for_load_state('networkidle')
        
        # organic results on DDG often have '[data-testid="result-title-a"]'
        results = page.locator("a[data-testid='result-title-a'], .result__a").all()
        print(f"  [Discovery] Found {len(results)} search results.")
        
        for result in results:
            try:
                href = result.get_attribute("href")
                text = (result.inner_text() or "").strip()
                if not href or not href.startswith("http"): continue
                if "duckduckgo.com" in href: continue
                
                print(f"  [Discovery] Checking result: {text} ({href})")
                
                # Broadly match if it looks like the bank or banking
                keywords = ["login", "banking", "online", "portal", "retail", "ebl", "nic", "nabil", "omni", "mobank", "mobile"]
                if any(k in href.lower() or k in text.lower() for k in keywords):
                    print(f"  [Discovery] ✅ Matched Result: {text}. Clicking...")
                    result.scroll_into_view_if_needed()
                    result.highlight()
                    page.wait_for_timeout(1500)
                    result.click()
                    page.wait_for_load_state('networkidle', timeout=30000)
                    return page.url # Return where we actually landed
            except: continue
    except Exception as e:
        print(f"  [Discovery] Discovery failed: {e}")
    return None

def _handle_landing_page_login(page: Page) -> bool:
    """Looks for 'Login', 'eBanking', or 'Retail' buttons on a bank's landing page."""
    print("  [Step] Landed on home page. Looking for login portal button...")
    login_selectors = [
        "a:has-text('Login')", "button:has-text('Login')", 
        "a:has-text('eBanking')", "a:has-text('Internet Banking')",
        "a:has-text('Retail')", "a:has-text('Online Banking')",
        "a:has-text('MoBank')", "a:has-text('Mobile Banking')",
        ".login-btn", "#login-button", "[class*='login']", "[id*='login']",
        "header a[href*='omni']", "a:has-text('Login/Register')"
    ]
    
    for sel in login_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                print(f"  [Demo] Found login button: '{el.inner_text().strip()}'. Clicking...")
                el.highlight()
                page.wait_for_timeout(1000)
                el.click()
                page.wait_for_load_state('networkidle', timeout=30000)
                return True
        except:
            continue
    return False

def _find_login_fields(page: Page) -> dict:
    """Heuristically identifies username and password fields on a page."""
    selectors = {
        "user_sel": "input[placeholder*='Mobile'], input[placeholder*='mobile'], input[name*='phone'], input[id*='phone'], input[type='text'], input[name*='user'], input[id*='user']",
        "pass_sel": "input[type='password'], input[placeholder*='Password'], input[placeholder*='password']",
        "submit_sel": "button:has-text('Log In'), button:has-text('Login'), button:has-text('Sign In'), button.nd-button--primary, button[type='submit'], input[type='submit']"
    }
    
    found = {}
    for key, sel in selectors.items():
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=5000):
                # If there are multiple fields, we might need more specific logic, 
                # but for most banks, the first match is usually correct for user/pass.
                found[key] = sel
        except:
            continue
    return found

def _poll_for_otp(account_id: int, timeout_mins: int = 5) -> str | None:
    """Polls the backend (via API or Direct DB) for a new OTP for the given account."""
    api_base = os.getenv("API_BASE_URL", "https://ipoautomation.vercel.app/api")
    token = os.getenv("API_TOKEN")
    db_url = os.getenv("DATABASE_URL")
    
    if not token and not db_url:
        print("  [OTP] API_TOKEN and DATABASE_URL not set. Cannot poll for OTP.")
        return None

    print(f"  [OTP] Waiting up to {timeout_mins} minutes for OTP relay (Account ID: {account_id})...")
    start_time = time.time()
    
    while time.time() - start_time < timeout_mins * 60:
        try:
            # Plan A: Use REST API (Vercel/Cloud)
            if token:
                response = requests.get(
                    f"{api_base}/bank-otps/?account={account_id}&is_used=false",
                    headers={"Authorization": f"Token {token}"},
                    timeout=10
                )
                if response.status_code == 200:
                    otps = response.json()
                    if otps:
                        latest_otp = otps[0]
                        requests.patch(
                            f"{api_base}/bank-otps/{latest_otp['id']}/",
                            json={"is_used": True},
                            headers={"Authorization": f"Token {token}"}
                        )
                        return latest_otp['otp_code']
            
            # Plan B: Direct Database Query (Local/Heroku/Server)
            elif db_url:
                import psycopg2
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                cur.execute(
                    "SELECT otp_code, id FROM automation_bankotp "
                    "WHERE account_id = %s AND is_used = false "
                    "ORDER BY created_at DESC LIMIT 1", 
                    (account_id,)
                )
                res = cur.fetchone()
                if res:
                    otp_code, otp_id = res
                    cur.execute("UPDATE automation_bankotp SET is_used = true WHERE id = %s", (otp_id,))
                    conn.commit()
                    conn.close()
                    return otp_code
                conn.close()
                
        except Exception as e:
            print(f"  ⚠️  Error polling for OTP: {e}")
        
        time.sleep(10) # Poll every 10 seconds
    
    print("  [OTP] OTP polling timed out.")
    return None

def check_balance(bank_code: str, phone_number: str, password: str, page: Page, account_id: int = None) -> float | None:
    """
    Generic balance checker.
    Returns the available balance as a float, or None if it cannot be determined.
    """
    config = BANK_CONFIGS.get(bank_code)
    
    # --- Dynamic Discovery ---
    # If no config or no URL, try to discover
    target_url = config.get('url') if config else None
    if not target_url:
        print(f"  ⚠️  No saved URL for '{bank_code}'. Attempting discovery...")
        target_url = _discover_login_page(bank_code.replace('_', ' ').title(), page)
    
    if not target_url:
        print(f"  ❌ Could not find a login page for '{bank_code}'. Skipping.")
        return None

    print(f"  🏦 Accessing {bank_code.replace('_', ' ').title()} at {target_url}...")
    try:
        page.goto(target_url, timeout=60000)
        page.wait_for_load_state('networkidle', timeout=30000)

        # Handle potential location/overlay prompt
        # User requested to click 'Allow while using this site'
        try:
            loc_prompts = [
                "button:has-text('Allow')", 
                "button:has-text('Allow while visiting')", 
                "button:has-text('Allow while using')",
                "button:has-text('Accept')",
                ".allow-button",
                "#allow-location"
            ]
            for sel in loc_prompts:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=3000):
                    print(f"  [Overlay] Clicking location permission button: {sel}")
                    btn.click()
                    page.wait_for_timeout(1000)
                    break
        except:
            pass # No prompt visible, move on

        # Identify fields: use config if available, otherwise heuristics
        user_sel = config.get('user_sel') if config else None
        pass_sel = config.get('pass_sel') if config else None
        submit_sel = config.get('submit_sel') if config else None

        if not (user_sel and pass_sel):
            print("  🧩 Identifying login fields via heuristics (waiting 3s for form)...")
            page.wait_for_timeout(3000)
            fields = _find_login_fields(page)
            user_sel = fields.get('user_sel')
            pass_sel = fields.get('pass_sel')
            submit_sel = fields.get('submit_sel')

        # If fields still not found, we might be on a landing page
        if not (user_sel and pass_sel):
            if _handle_landing_page_login(page):
                # Try discovery again after clicking login button
                fields = _find_login_fields(page)
                user_sel = fields.get('user_sel')
                pass_sel = fields.get('pass_sel')
                submit_sel = fields.get('submit_sel')

        if not (user_sel and pass_sel):
            print("  ❌ Could not identify login fields. Page structure might be too complex.")
            return None

        # Angular-aware login: wait explicitly for field to be interactive, then click and type
        print(f"  [Login] Waiting for username field to be visible and interactable...")
        try:
            page.wait_for_selector(user_sel, state="visible", timeout=30000)
        except Exception as e:
            print(f"  ❌ Username field never appeared: {e}")
            return None

        print(f"  [Login] Clicking and typing phone number...")
        page.locator(user_sel).first.click()
        page.wait_for_timeout(500)
        page.locator(user_sel).first.fill("")
        page.locator(user_sel).first.type(phone_number, delay=80)
        page.wait_for_timeout(1000)

        # If password field is not visible, we might need to click 'Proceed' first
        if not page.locator(pass_sel).is_visible():
            proceed_sel = config.get('proceed_sel') if config else None
            if proceed_sel and page.locator(proceed_sel).is_visible():
                print("  [Step] Clicking 'Proceed' for multi-step login...")
                page.click(proceed_sel)
                page.wait_for_timeout(2000)
            elif submit_sel and page.locator(submit_sel).is_visible():
                 print("  [Step] Clicking 'Submit/Proceed' for multi-step login...")
                 page.click(submit_sel)
                 page.wait_for_timeout(2000)

        page.wait_for_selector(pass_sel, state="visible", timeout=15000)
        print(f"  [Login] Clicking and typing password...")
        page.locator(pass_sel).first.click()
        page.wait_for_timeout(500)
        page.locator(pass_sel).first.fill("")
        page.locator(pass_sel).first.type(password, delay=80)
        page.wait_for_timeout(1000)
        
        print("  [Login] Submitting form...")
        final_submit = submit_sel if submit_sel else "button[type='submit']"
        if page.locator(final_submit).first.is_visible():
            page.locator(final_submit).first.click()
        else:
            page.keyboard.press("Enter")
        
        # --- OTP / Approval Handling ---
        print("  [OTP/Approve] Checking for interaction prompt (waiting up to 15s)...")
        
        # Check for push approval notification (common in NIC Asia MoBank)
        # We also check for "Verify Login" text which is the header for NIC Asia's OTP page
        page.wait_for_load_state('networkidle', timeout=15000)
        page_text = page.inner_text('body').lower()
        
        is_otp_screen = "verify login" in page_text or "verification code" in page_text
        if is_otp_screen:
            print("  [OTP] OTP/Verification screen detected by page text.")

        if "approve" in page_text or "notification" in page_text or "mobile app" in page_text:
            print("  [Approve] Mobile app approval prompt detected. Please tap 'Approve' on your MoBank app.")
            print("  [Approve] Waiting up to 60s for approval...")
            try:
                page.wait_for_load_state('networkidle', timeout=60000)
            except: pass
        
        otp_selectors = [
            ".otp-field__input", "input[placeholder='*']", 
            "input[name*='otp']", "input[id*='otp']", "input[placeholder*='OTP']", 
            "input[name*='code']", "input[id*='txtOTP']", "input[placeholder*='Code']"
        ]
        
        found_otp_field = False
        target_otp_sel = None
        for otp_sel in otp_selectors:
            try:
                if page.locator(otp_sel).first.is_visible(timeout=5000):
                    found_otp_field = True
                    target_otp_sel = otp_sel
                    print(f"  [OTP] OTP field detected ({otp_sel}).")
                    break
            except: continue

        if found_otp_field or is_otp_screen:
            if not found_otp_field:
                # Fallback to general input if text matched but selector didn't
                target_otp_sel = "input:not([type='hidden'])"
            
            print(f"  [OTP] OTP required for {config.get('name', 'Bank')} login.")
            if account_id:
                otp_code = _poll_for_otp(account_id)
                if otp_code:
                    print(f"  [OTP] OTP received: {otp_code}. Entering...")
                    # For multi-box inputs like NIC Asia, we might need to type slowly
                    first_input = page.locator(target_otp_sel).first
                    first_input.click()
                    page.wait_for_timeout(500)
                    page.keyboard.type(otp_code, delay=200)
                    page.wait_for_timeout(1000)
                    page.keyboard.press("Enter")
                    
                    # Some banks need a "Continue" click
                    try:
                        page.click("button:has-text('Continue'), button:has-text('Verify')", timeout=5000)
                    except: pass
                    
                    page.wait_for_load_state('networkidle', timeout=30000)
                else:
                    print("  [OTP] Failed to get OTP. Login aborted.")
                    return None
            else:
                print("  [OTP] account_id not provided. Cannot poll for OTP.")
                # We still wait a bit in case they enter it manually
                page.wait_for_timeout(10000)

        # Final check if we are on the dashboard
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(3) # Wait for dashboard to settle

        # Try mapping-specific selectors
        # Try specific selectors from config first
        if config.get("balance_sel"):
            for sel in config["balance_sel"]:
                try:
                    elem = page.locator(sel).first
                    if elem.is_visible(timeout=5000):
                        text = elem.inner_text()
                        balance = _extract_balance(text)
                        if balance is not None:
                            print(f"  [Balance] Found via selector '{sel}': Rs. {balance:,.2f}")
                            return balance
                except: continue

        # Keyword based search
        try:
            # We look for "Available Balance" FIRST as it's the most accurate
            prioritized_keywords = ["Available Balance", "Available", "Total Balance", "Balance", "Amount"]
            for kw in prioritized_keywords:
                labels = page.get_by_text(kw, exact=True).all()
                if not labels:
                     labels = page.get_by_text(kw, exact=False).all()
                
                for label in labels:
                    try:
                        if label.is_visible():
                            # Look at the parent or next sibling
                            parent_text = label.locator("xpath=..").inner_text()
                            balance = _extract_balance(parent_text)
                            if balance is not None:
                                print(f"  [Balance Debug] Found '{kw}' in parent text: '{parent_text.strip()}' -> Rs. {balance:,.2f}")
                                return balance
                            
                            # Try next sibling
                            sibling_text = page.evaluate("(el) => el.nextElementSibling ? el.nextElementSibling.innerText : ''", label.element_handle())
                            balance = _extract_balance(sibling_text)
                            if balance is not None:
                                 print(f"  [Balance Debug] Found '{kw}' in sibling text: '{sibling_text.strip()}' -> Rs. {balance:,.2f}")
                                 return balance
                    except: continue
        except: pass

        # Fallback: Regex scraper for currency-like strings
        print("  [Balance Debug] Falling back to regex scraper...")
        content = page.content()
        clean_content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)
        clean_content = re.sub(r'<style.*?>.*?</style>', '', clean_content, flags=re.DOTALL)
        
        # Look for Rs. X,XXX.XX or NPR X,XXX.XX
        matches = re.findall(r'(?:Rs\.?|NPR|Amount)\s*([\d,]+\.\d{2})', clean_content)
        if not matches:
             # Look for any digit with commas and 2 decimal places
             matches = re.findall(r'[\d,]+\.\d{2}', clean_content)

        print(f"  [Balance Debug] Found {len(matches)} potential currency matches: {matches}")
        
        valid_balances = []
        for m in matches:
            try:
                val = float(m.replace(',', ''))
                # Threshold to avoid small IDs or huge account numbers
                if 5.0 <= val <= 5000000.0:
                    context_match = re.search(r'(.{0,40})' + re.escape(m) + r'(.{0,40})', clean_content)
                    context_text = context_match.group(0).replace('\n', ' ') if context_match else "No context"
                    print(f"  [Balance Debug] Candidate: {m} (Context: ...{context_text}...)")
                    valid_balances.append(val)
            except: pass

        if valid_balances:
            # Usually the largest currency amount on a dashboard is the balance if multiple exist
            # but for NIC Asia, it's often the first one under 'Available'
            return valid_balances[0]

    except Exception as e:
        print(f"  [Error] Balance check failed for {config['name']}: {e}")
    finally:
        # ALWAYS take a screenshot of the dashboard for verification
        try:
            shots_dir = "d:\\ipoautomation\\screenshots"
            if not os.path.exists(shots_dir): os.makedirs(shots_dir)
            t_stamp = int(time.time())
            path = os.path.join(shots_dir, f"dashboard_{config.get('name','bank')}_{t_stamp}.png")
            page.screenshot(path=path, full_page=True)
            print(f"  [Debug] Dashboard screenshot saved to: {path}")
        except: pass

    return None
