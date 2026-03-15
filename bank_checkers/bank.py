"""
bank_checkers/bank.py
---------------------
Config-driven multi-bank balance checker for Nepali internet banking portals.
"""

from playwright.sync_api import Page
import re, time, requests, os
from datetime import datetime, timezone, timedelta

# -------------------------------------------------------------------
# Bank registry (Comprehensive mapping for Class A & B banks)
# -------------------------------------------------------------------
BANK_CONFIGS: dict[str, dict] = {
    # --- Commercial Banks (Class A) ---
    "nic_asia": {
        "name": "NIC Asia Bank",
        "url": "https://omni.nicasiabank.com/sign-in",
        "user_sel": ["#nd-input-1", "input[placeholder='Enter Mobile Number']"],
        "pass_sel": ["#nd-input-0", "input[placeholder='Enter Password']", "input[type='password']"],
        "submit_sel": ["button.nd-button--primary", "button:has-text('Log In')"],
        "dashboard_sel": [".nd-dashboard", ".nd-account-card", ".available-balance", "app-dashboard", ".nd-account-list", "nd-card", "app-root .main-view"],
        "balance_sel": ["span.balance-amount", ".available-balance", ".amt-balance", ".nd-balance-value", ".total-balance", ".account-card__balance"],
        "otp_ident": ["Verify Login", "Verification Code", "Enter OTP"],
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
        # Relax the start time (allow OTPs from 2 mins ago to handle slow navigation/race conditions)
    poll_start_time = datetime.now(timezone.utc) - timedelta(minutes=2)
    start_time_unix = time.time()
    
    # We increase the polling frequency at the start and slow down
    while time.time() - start_time_unix < timeout_mins * 60:
        try:
            # Plan A: Use REST API (Best for Cloud/Vercel)
            if token:
                response = requests.get(
                    f"{api_base}/bank-otps/?is_used=false",
                    headers={"Authorization": f"Token {token}"},
                    timeout=10
                )
                if response.status_code == 200:
                    otps = response.json()
                    # Filter for our account or orphaned background codes (null account_id)
                    for otp in otps:
                        created_at_dt = None
                        try:
                            c_str = otp.get('created_at', '')
                            created_at_dt = datetime.fromisoformat(c_str.replace('Z', '+00:00'))
                        except: pass

                        if not created_at_dt or created_at_dt >= poll_start_time:
                            # Match if correct account OR orphaned background relay (null)
                            if otp.get('account_id') in (account_id, None):
                                print(f"  [OTP] Found code {otp['otp_code']} (Created: {otp.get('created_at')})")
                                requests.patch(
                                    f"{api_base}/bank-otps/{otp['id']}/",
                                    json={"is_used": True},
                                    headers={"Authorization": f"Token {token}"}
                                )
                                return otp['otp_code']
            
            # Plan B: Direct Database Query (Fastest for local/Heroku)
            if db_url:
                import psycopg2
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                # Include account_id = NULL but ONLY for the same user (catch orphaned background relays)
                cur.execute(
                    "SELECT otp_code, id, created_at FROM automation_bankotp "
                    "WHERE (account_id = %s OR (account_id IS NULL AND user_id = (SELECT owner_id FROM automation_account WHERE id = %s))) "
                    "AND is_used = false AND created_at >= %s "
                    "ORDER BY created_at DESC LIMIT 1", 
                    (account_id, account_id, poll_start_time)
                )
                res = cur.fetchone()
                if res:
                    otp_code, otp_id, created_at = res
                    print(f"  [OTP] Found code {otp_code} in DB (ID: {otp_id}, Created: {created_at})")
                    cur.execute("UPDATE automation_bankotp SET is_used = true WHERE id = %s", (otp_id,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    return otp_code
                cur.close()
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
            # Handle list or string for wait_for_selector
            target_user = ", ".join(user_sel) if isinstance(user_sel, list) else user_sel
            page.wait_for_selector(target_user, state="visible", timeout=30000)
        except Exception as e:
            print(f"  ❌ Username field never appeared: {e}")
            return None

        print(f"  [Login] Clicking and typing phone number...")
        user_locator = page.locator(", ".join(user_sel) if isinstance(user_sel, list) else user_sel).first
        user_locator.click()
        page.wait_for_timeout(500)
        user_locator.fill("")
        user_locator.type(phone_number, delay=80)
        page.wait_for_timeout(1000)

        # If password field is not visible, we might need to click 'Proceed' first
        target_pass = ", ".join(pass_sel) if isinstance(pass_sel, list) else pass_sel
        if not page.locator(target_pass).first.is_visible():
            proceed_sel = config.get('proceed_sel') if config else None
            # proceed_sel can be a list too
            target_proceed = ", ".join(proceed_sel) if isinstance(proceed_sel, list) else proceed_sel
            
            if target_proceed and page.locator(target_proceed).first.is_visible():
                print("  [Step] Clicking 'Proceed' for multi-step login...")
                page.locator(target_proceed).first.click()
                page.wait_for_timeout(2000)
            elif submit_sel:
                target_submit = ", ".join(submit_sel) if isinstance(submit_sel, list) else submit_sel
                if page.locator(target_submit).first.is_visible():
                    print("  [Step] Clicking 'Submit/Proceed' for multi-step login...")
                    page.locator(target_submit).first.click()
                    page.wait_for_timeout(2000)

        page.wait_for_selector(target_pass, state="visible", timeout=15000)
        print(f"  [Login] Clicking and typing password...")
        pass_locator = page.locator(target_pass).first
        pass_locator.click()
        page.wait_for_timeout(500)
        pass_locator.fill("")
        pass_locator.type(password, delay=80)
        page.wait_for_timeout(1000)
        
        print("  [Login] Submitting form...")
        target_final_submit = ", ".join(submit_sel) if isinstance(submit_sel, list) else (submit_sel if submit_sel else "button[type='submit']")
        
        final_submit_locator = page.locator(target_final_submit).first
        if final_submit_locator.is_visible():
            final_submit_locator.click()
        else:
            page.keyboard.press("Enter")
        
        # --- OTP / Approval Handling ---
        print("  [OTP/Approve] Polling for OTP screen or Dashboard (up to 30s)...")
        
        is_otp_screen = False
        start_wait = time.time()
        while time.time() - start_wait < 30:
            try:
                page_text = page.inner_text('body').lower()
                # Check for OTP keywords
                otp_keywords = config.get('otp_ident', ["verify login", "verification code", "enter otp", "enter code"])
                if any(kw.lower() in page_text for kw in otp_keywords) or "/verify" in page.url or "/otp" in page.url:
                    is_otp_screen = True
                    print(f"  [OTP] OTP/Verification screen detected (URL: {page.url})")
                    break
                
                # Check if we already reached dashboard
                dash_sels = config.get("dashboard_sel", [".dashboard"])
                dash_sel = ", ".join(dash_sels) if isinstance(dash_sels, list) else dash_sels
                if page.locator(dash_sel).first.is_visible():
                    print("  [Login] Dashboard reached directly.")
                    break
                    
                page.wait_for_timeout(2000)
            except: 
                page.wait_for_timeout(2000)

        if is_otp_screen:
            print("  [OTP] OTP/Verification screen confirmed. Proceeding with polling...")
        if "approve" in page_text or "notification" in page_text or "mobile app" in page_text:
            print("  [Approve] Mobile app approval prompt detected. Please tap 'Approve' on your MoBank app.")
            print("  [Approve] Waiting up to 90s for approval...")
            try:
                # Wait for navigation or dashboard to appear after approval
                dash_sel = config.get("dashboard_sel", ".dashboard")
                page.wait_for_selector(dash_sel, state="visible", timeout=90000)
                print("  [Approve] Dashboard detected after approval!")
            except: 
                print("  [Approve] Dashboard not detected after 90s. Checking for OTP field...")
                pass
        
        otp_selectors = [
            "#otp", "input[name*='otp']", "input[id*='otp']", "input[placeholder*='OTP']",
            ".otp-field__input", "input[placeholder='*']", 
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
        # Wait for a "Dashboard" specific element before scraping balance
        dashboard_sel = config.get("dashboard_sel", ".dashboard, .account-summary, .available-balance")
        print(f"  [Dashboard] Waiting for dashboard ({dashboard_sel})...")
        try:
            if isinstance(dashboard_sel, list):
                page.wait_for_selector(", ".join(dashboard_sel), state="visible", timeout=45000)
            else:
                page.wait_for_selector(dashboard_sel, state="visible", timeout=45000)
            time.sleep(5) # Wait for dashboard to settle
            
            # Additional check for loading overlays
            try:
                page.wait_for_selector(".loading-overlay, .spinner, .nd-loader", state="hidden", timeout=5000)
            except: pass
        except:
             print("  ⚠️ Dashboard not detected via selector. Diagnostics:")
             print(f"  [Debug] Current URL: {page.url}")
             try:
                 txt = page.inner_text('body')[:300].replace('\n', ' ')
                 print(f"  [Debug] Page text (start): {txt}")
             except: pass
             print("  Proceeding with fallback scraping...")

        # Try mapping-specific selectors
        balance_sels = config.get("balance_sel")
        if balance_sels:
            # Handle both list and comma-separated string
            if isinstance(balance_sels, str):
                balance_sels = [s.strip() for s in balance_sels.split(",")]
            
            for sel in balance_sels:
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
            # We also ensure the page is actually showing dashboard-like text
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
        # Use inner_text to avoid technical numbers in HTML attributes (like versions)
        clean_content = page.inner_text('body')
        
        # 1. Look for Rs. X,XXX.XX or NPR X,XXX.XX (Most accurate)
        matches = re.findall(r'(?:Rs\.?|NPR|Amount|Total|Available)\s*([\d,]+\.\d{2})\b', clean_content, re.IGNORECASE)
        
        if not matches:
             # 2. Look for any digit with commas and 2 decimal places with word boundaries
             matches = re.findall(r'\b[\d,]+\.\d{2}\b', clean_content)

        print(f"  [Balance Debug] Found {len(matches)} potential currency matches: {matches}")
        
        valid_balances = []
        for m in matches:
            try:
                # Sanitize commas
                clean_m = m.replace(',', '')
                # Avoid capturing '1,234.567' as '1,234.56' by checking word boundaries or strictly
                val = float(clean_m)
                
                # Filter out numbers that are likely not balances (too small or exact whole thousands usually)
                # But a balance of 5.00 is possible. Let's at least check context.
                if 2.0 <= val <= 10000000.0:
                    context_match = re.search(r'(.{0,30})' + re.escape(m) + r'(.{0,30})', clean_content)
                    context_text = context_match.group(0).replace('\n', ' ').strip() if context_match else "No context"
                    
                    # Heuristic: skip if context looks like SVG/CSS/Technical
                    if any(x in context_text.lower() for x in ["px", "transform", "color", "width", "height", "viewbox", "rect"]):
                        continue
                        
                    print(f"  [Balance Debug] Candidate: {m} (Context: ...{context_text}...)")
                    valid_balances.append(val)
            except: pass

        if valid_balances:
            # Usually the first found amount on a dashboard (after stripping headers) is the main balance
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
