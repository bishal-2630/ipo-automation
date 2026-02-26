"""
expiry_handler.py
-----------------
Handles DEMAT and MeroShare account expiry detection for the IPO automation.
KYC expiry is intentionally excluded — only DEMAT and MeroShare account status
is monitored here.
"""

from notifications import send_email_notification


DEMAT_EXPIRY_KEYWORDS = [
    "demat account expired",
    "demat account has expired",
    "demat account is expired",
    "demat account suspended",
    "demat account has been suspended",
    "renew your demat",
    "demat renewal",
    "demat account renewal required",
]

MEROSHARE_EXPIRY_KEYWORDS = [
    "meroshare account expired",
    "meroshare account has expired",
    "your account has expired",
    "account is expired",
    "account has been deactivated",
    "account deactivated",
    "account suspended",
    "your account is suspended",
    "account is inactive",
    "inactive account",
]


EXPIRY_WARNING_PATTERNS = [
    "demat expires on",
    "demat expiry",
    "demat valid till",
    "demat renewal due",
    "account expires on",
    "account expiry",
    "account valid till",
    "account renewal due",
]


def detect_account_expiry(page, username):
    """
    Scans the current page HTML for DEMAT or MeroShare account expiry messages.

    Returns:
        'DEMAT_EXPIRED'      — if a DEMAT account expiry keyword is found
        'MEROSHARE_EXPIRED'  — if a MeroShare account expiry keyword is found
        None                 — if no expiry is detected
    """
    try:
        page_text = page.content().lower()

        for kw in DEMAT_EXPIRY_KEYWORDS:
            if kw in page_text:
                print(f"[{username}] ⚠️ DEMAT expiry detected: '{kw}'")
                return "DEMAT_EXPIRED"

        for kw in MEROSHARE_EXPIRY_KEYWORDS:
            if kw in page_text:
                print(f"[{username}] ⚠️ MeroShare account expiry detected: '{kw}'")
                return "MEROSHARE_EXPIRED"

    except Exception as e:
        print(f"[{username}] Warning: Could not scan for account expiry: {e}")

    return None


def check_account_expiry_warning(page, account):
    """
    Should be called after a successful login, before applying or checking IPOs.
    Scans the dashboard text for *upcoming* DEMAT / MeroShare account expiry
    hints (e.g. "account expires on DD/MM/YYYY") and sends a proactive email
    with the expiry date and days remaining.

    KYC warnings are intentionally excluded.
    """
    import re
    from datetime import datetime, date

    username = account["MEROSHARE_USER"]
    try:
        patterns_js = str(EXPIRY_WARNING_PATTERNS).replace("'", '"')

        # Extract a wider snippet (150 chars) so a nearby date is captured too
        result = page.evaluate(f"""
            () => {{
                const body = document.body.innerText.toLowerCase();
                const patterns = {patterns_js};
                for (const p of patterns) {{
                    const idx = body.indexOf(p);
                    if (idx !== -1) return body.substring(Math.max(0, idx - 10), idx + 150);
                }}
                return null;
            }}
        """)

        if not result:
            return

        print(f"[{username}] ⚠️ Upcoming expiry warning detected: {result.strip()}")

        # Try to extract a date from the snippet (supports DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY)
        expiry_date = None
        days_left_str = ""
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',   # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',   # DD/MM/YYYY
            r'(\d{2}-\d{2}-\d{4})',   # DD-MM-YYYY
        ]
        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']

        for pattern, fmt in zip(date_patterns, date_formats):
            match = re.search(pattern, result)
            if match:
                try:
                    expiry_date = datetime.strptime(match.group(1), fmt).date()
                    days_left = (expiry_date - date.today()).days
                    if days_left >= 0:
                        days_left_str = f"  📅 Expires on: {expiry_date.strftime('%d %B %Y')} ({days_left} day(s) remaining)\n"
                    else:
                        days_left_str = f"  📅 Expired on: {expiry_date.strftime('%d %B %Y')} ({abs(days_left)} day(s) ago)\n"
                    break
                except ValueError:
                    pass

        if not days_left_str:
            # No parseable date found — include raw snippet
            days_left_str = f"  ℹ️ Details: {result.strip()}\n"

        send_email_notification(
            account.get("EMAIL"),
            "[MeroShare] ⚠️ Account Expiry Warning",
            f"Hi {username},\n\n"
            f"An upcoming DEMAT or MeroShare account expiry was detected on your dashboard:\n\n"
            f"{days_left_str}\n"
            f"Please log in to https://meroshare.cdsc.com.np and renew your account "

        )

    except Exception as e:
        print(f"[{username}] Warning: Could not check expiry warning: {e}")


def handle_expired_account(account, expiry_type):
    """
    Sends the appropriate email for a hard-expired account and returns False
    so the caller knows to skip further processing for this account.

    Args:
        account     — the account dict (must contain 'MEROSHARE_USER' and 'EMAIL')
        expiry_type — 'DEMAT_EXPIRED' or 'MEROSHARE_EXPIRED'

    Returns:
        False (always) — signals that the account should be skipped
    """
    username = account.get("MEROSHARE_USER")

    if expiry_type == "DEMAT_EXPIRED":
        print(f"[{username}] ❌ DEMAT account expired. Skipping.")
        send_email_notification(
            account.get("EMAIL"),
            "[MeroShare] Action Required: DEMAT Account Expired",
            f"Hi {username},\n\n"
            f"Your DEMAT account has expired on MeroShare.\n"
            f"Please renew it in time.\n\n"
        )

    elif expiry_type == "MEROSHARE_EXPIRED":
        print(f"[{username}] ❌ MeroShare account expired/deactivated. Skipping.")
        send_email_notification(
            account.get("EMAIL"),
            "[MeroShare] Action Required: Account Expired",
            f"Hi {username},\n\n"
            f"Your MeroShare account appears to be expired.\n"
            f"Please visit https://meroshare.cdsc.com.np and renew it in time.\n\n"
        )

    return False
