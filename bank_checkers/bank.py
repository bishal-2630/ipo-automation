"""
bank_checkers/bank.py
---------------------
Config-driven multi-bank balance checker for Nepali internet banking portals.
"""

from playwright.sync_api import Page
import re, time

# -------------------------------------------------------------------
# Bank registry (Comprehensive mapping for Class A & B banks)
# -------------------------------------------------------------------
BANK_CONFIGS: dict[str, dict] = {
    # --- Commercial Banks (Class A) ---
    "nic_asia": {
        "name": "NIC Asia Bank",
        "url": "https://ebanking.nicasiabank.com",
        "user_sel": "input[name='username'], #username",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit'], input[type='submit']",
        "balance_sel": ".balance, [class*='balance'], [id*='balance']",
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
        "url": "https://ebanking.everestbankltd.com",
        "user_sel": "#userName",
        "pass_sel": "input[type='password']",
        "submit_sel": "button[type='submit']",
        "balance_sel": ".balance",
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

def check_balance(bank_code: str, phone_number: str, password: str, page: Page) -> float | None:
    """
    Generic balance checker.
    Returns the available balance as a float, or None if it cannot be determined.
    """
    config = BANK_CONFIGS.get(bank_code)
    if not config:
        # For banks not yet specifically mapped, we return None (don't block IPO)
        print(f"  ⚠️  Balance check not yet implemented for '{bank_code}'. Skipping.")
        return None

    print(f"  🏦 Checking balance for {config['name']}...")
    try:
        page.goto(config['url'], timeout=60000)
        page.wait_for_load_state('networkidle', timeout=30000)

        # Basic attempt at login (selectors might need fine-tuning per bank)
        page.fill(config['user_sel'], phone_number)
        page.fill(config['pass_sel'], password)
        page.click(config['submit_sel'])
        
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(3) # Wait for dashboard to settle

        # Try mapping-specific selectors
        for sel in config['balance_sel'].split(','):
            sel = sel.strip()
            if not sel: continue
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=5000):
                    balance = _extract_balance(el.text_content())
                    if balance is not None:
                        print(f"  💰 Found Balance: Rs. {balance:,.2f}")
                        return balance
            except Exception:
                continue

        # Fallback: Scrape anything that looks like NPR / Rs balance
        content = page.content()
        matches = re.findall(r'(?:Rs\.?|NPR|रु)\s*([\d,]+(?:\.\d+)?)', content)
        for m in matches:
            val = float(m.replace(',', ''))
            if val > 100: # Threshold to avoid tiny IDs
                print(f"  💰 Found Balance (Regex): Rs. {val:,.2f}")
                return val

    except Exception as e:
        print(f"  ❌ Balance check failed for {config['name']}: {e}")

    return None
