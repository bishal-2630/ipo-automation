import os
import psycopg2
import datetime
from playwright.sync_api import sync_playwright
from main import login, apply_ipo

# ── Firebase setup ──────────────────────────────────────────────────
import firebase_admin
from firebase_admin import credentials, messaging

def _init_firebase():
    if not firebase_admin._apps:
        # config/firebase_vcc.json is checked into the repo
        cred_path = os.path.join(os.path.dirname(__file__), "config", "firebase_vcc.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

def send_push_notification(fcm_tokens: list, title: str, body: str):
    """Send an FCM multicast notification to a list of tokens."""
    if not fcm_tokens:
        print("No FCM tokens – skipping notification.")
        return
    _init_firebase()
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=fcm_tokens,
    )
    try:
        response = messaging.send_multicast(message)
        print(f"FCM: {response.success_count} sent, {response.failure_count} failed.")
    except Exception as e:
        print(f"FCM error: {e}")

# ── Database connection ─────────────────────────────────────────────
DB_URL = os.environ.get("DATABASE_URL")

def run_automation():
    if not DB_URL:
        print("Error: DATABASE_URL not set.")
        return

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # 1. Fetch active accounts (include owner_id for notifications)
        cur.execute("""
            SELECT id, meroshare_user, meroshare_pass, dp_name, crn, tpin, bank_name, kitta, owner_id
            FROM automation_account
            WHERE is_active = True;
        """)
        columns = [desc[0] for desc in cur.description]
        accounts = [dict(zip(columns, row)) for row in cur.fetchall()]

        if not accounts:
            print("No active accounts found.")
            return

        print(f"Found {len(accounts)} active accounts. Starting automation...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for acc in accounts:
                print(f"\nProcessing: {acc['meroshare_user']}")
                page = browser.new_page()
                status = "Error"
                remark = "Unknown error"

                try:
                    account_data = {
                        'MEROSHARE_USER': acc['meroshare_user'],
                        'MEROSHARE_PASS': acc['meroshare_pass'],
                        'DP_NAME': acc['dp_name'],
                        'CRN': acc['crn'],
                        'TPIN': acc['tpin'],
                        'BANK_NAME': acc['bank_name'],
                        'KITTA': str(acc['kitta']),
                    }

                    page.goto("https://meroshare.cdsc.com.np", timeout=60000)
                    login_result = login(
                        page,
                        account_data['MEROSHARE_USER'],
                        account_data['MEROSHARE_PASS'],
                        account_data['DP_NAME'],
                    )

                    if login_result is True:
                        print(f"  ✅ Login OK. Applying IPO...")
                        apply_ipo(page, account_data)
                        status = "Success"
                        remark = "IPO applied successfully via GitHub Action"
                    else:
                        print(f"  ❌ Login failed: {login_result}")
                        status = "Failed"
                        remark = f"Login failed: {login_result}"

                except Exception as e:
                    print(f"  ❌ Exception: {e}")
                    status = "Error"
                    remark = str(e)

                finally:
                    # 2. Write log to DB
                    cur.execute("""
                        INSERT INTO automation_applicationlog
                            (account_id, company_name, status, remark, timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (acc['id'], "Auto-Check", status, remark, datetime.datetime.now(datetime.timezone.utc)))
                    conn.commit()

                    # 3. Send FCM push notification to account owner
                    if acc.get('owner_id'):
                        cur.execute(
                            "SELECT token FROM automation_fcmtoken WHERE user_id = %s",
                            (acc['owner_id'],)
                        )
                        tokens = [row[0] for row in cur.fetchall()]
                        notif_title = "✅ IPO Applied!" if status == "Success" else f"⚠️ IPO {status}"
                        notif_body = f"{acc['meroshare_user']}: {remark}"
                        send_push_notification(tokens, notif_title, notif_body)

                    page.close()

            browser.close()

        cur.close()
        conn.close()
        print("\nAutomation run completed.")

    except Exception as e:
        print(f"DB Error: {e}")


if __name__ == "__main__":
    run_automation()
