import os
import psycopg2
import datetime
from playwright.sync_api import sync_playwright
from main import login, apply_ipo
from bank_checkers.bank import check_balance

# ── Firebase setup ──────────────────────────────────────────────────
import firebase_admin
from firebase_admin import credentials, messaging

MIN_BALANCE = 2000.0  # Minimum required balance to apply for IPO (Rs.)

def _init_firebase():
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), "config", "firebase_vcc.json")
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            # Fallback: load from base64-encoded env variable (used on GitHub Actions)
            import base64, json, tempfile
            b64 = os.environ.get("FIREBASE_CREDENTIALS_B64", "")
            if not b64:
                print("  ⚠️  Firebase credentials not found (no file and no FIREBASE_CREDENTIALS_B64 env var). Skipping notifications.")
                return
            cred_json = json.loads(base64.b64decode(b64).decode())
            cred = credentials.Certificate(cred_json)
        firebase_admin.initialize_app(cred)

def send_push_notification(fcm_tokens: list, title: str, body: str):
    if not fcm_tokens:
        print("  No FCM tokens – skipping notification.")
        return
    _init_firebase()
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=fcm_tokens,
    )
    try:
        response = messaging.send_multicast(message)
        print(f"  FCM: {response.success_count} sent, {response.failure_count} failed.")
    except Exception as e:
        print(f"  FCM error: {e}")

# ── Database connection ─────────────────────────────────────────────
DB_URL = os.environ.get("DATABASE_URL")

# ── Encryption ─────────────────────────────────────────────────────
from cryptography.fernet import Fernet

_ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "").encode()

def decrypt(token: str) -> str:
    if not token or not _ENCRYPTION_KEY:
        return token
    try:
        return Fernet(_ENCRYPTION_KEY).decrypt(token.encode()).decode()
    except Exception:
        return token  # Not encrypted yet, return as-is

# ── Main automation ─────────────────────────────────────────────────

def run_automation():
    if not DB_URL:
        print("Error: DATABASE_URL not set.")
        return

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # 1. Fetch active accounts
        cur.execute("""
            SELECT a.id, a.meroshare_user, a.meroshare_pass, a.dp_name,
                   a.crn, a.tpin, a.bank_name, a.kitta, a.owner_id,
                   b.bank, b.phone_number, b.bank_password
            FROM automation_account a
            LEFT JOIN automation_bankaccount b ON b.linked_account_id = a.id
            WHERE a.is_active = True;
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
                print(f"\n{'='*50}")
                print(f"Processing: {acc['meroshare_user']}")
                page = browser.new_page()
                status = "Error"
                remark = "Unknown error"
                ipo_name = "Auto-Check"  # Always initialise before try/finally

                try:
                    # 2. Bank balance check (if bank credentials are linked)
                    if acc.get('bank') and acc.get('phone_number') and acc.get('bank_password'):
                        bank_page = browser.new_page()
                        try:
                            balance = check_balance(
                                bank_code=acc['bank'],
                                phone_number=acc['phone_number'],
                                password=decrypt(acc['bank_password']),
                                page=bank_page,
                            )
                        except Exception as bank_err:
                            print(f"  ⚠️  Bank balance check raised exception: {bank_err}. Proceeding with IPO.")
                            balance = None
                        finally:
                            bank_page.close()

                        if balance is not None and balance < MIN_BALANCE:
                            print(f"  ⚠️  Balance Rs.{balance:.2f} < Rs.{MIN_BALANCE:.2f} — skipping IPO.")
                            status = "Skipped"
                            remark = f"Insufficient balance: Rs.{balance:.2f} (min Rs.{MIN_BALANCE:.2f})"

                            # Notify account holder
                            if acc.get('owner_id'):
                                cur.execute(
                                    "SELECT token FROM automation_fcmtoken WHERE user_id = %s",
                                    (acc['owner_id'],)
                                )
                                tokens = [row[0] for row in cur.fetchall()]
                                send_push_notification(
                                    tokens,
                                    "⚠️ Low Bank Balance!",
                                    f"{acc['meroshare_user']}: Rs.{balance:.2f} balance. Please top up to apply for IPO.",
                                )

                            # Log and move on to next account
                            cur.execute("""
                                INSERT INTO automation_applicationlog
                                    (account_id, company_name, status, remark, timestamp, is_read)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (acc['id'], "Balance Check", status, remark,
                                  datetime.datetime.now(datetime.timezone.utc), False))
                            conn.commit()
                            page.close()
                            continue

                    # 3. Apply IPO via MeroShare
                    account_data = {
                        'MEROSHARE_USER': acc['meroshare_user'],
                        'MEROSHARE_PASS': decrypt(acc['meroshare_pass']),
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
                        success, result_detail = apply_ipo(page, account_data)
                        if success:
                            status = "Success"
                            ipo_name = result_detail
                            remark = f"{ipo_name} ipo has been applied successfully."
                        else:
                            status = "Failed"
                            remark = result_detail
                    else:
                        print(f"  ❌ Login failed: {login_result}")
                        status = "Failed"
                        remark = f"Login failed: {login_result}"

                except Exception as e:
                    print(f"  ❌ Exception: {e}")
                    status = "Error"
                    remark = str(e)

                finally:
                    # 4. Write log and send notification — wrapped so a DB error here
                    #    does NOT prevent the next account from being processed.
                    try:
                        cur.execute("""
                            INSERT INTO automation_applicationlog
                                (account_id, company_name, status, remark, timestamp, is_read)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (acc['id'], ipo_name, status, remark,
                              datetime.datetime.now(datetime.timezone.utc), False))
                        conn.commit()
                    except Exception as db_err:
                        print(f"  ⚠️  DB log error for {acc['meroshare_user']}: {db_err}")
                        try:
                            conn.rollback()
                        except Exception:
                            pass

                    try:
                        if acc.get('owner_id'):
                            cur.execute(
                                "SELECT token FROM automation_fcmtoken WHERE user_id = %s",
                                (acc['owner_id'],)
                            )
                            tokens = [row[0] for row in cur.fetchall()]
                            if status == "Success":
                                notif_title = "✅ IPO Applied!"
                                notif_body = remark
                            else:
                                notif_title = f"⚠️ IPO {status}"
                                notif_body = f"{acc['meroshare_user']}: {remark}"
                            send_push_notification(tokens, notif_title, notif_body)
                    except Exception as notif_err:
                        print(f"  ⚠️  Notification error for {acc['meroshare_user']}: {notif_err}")

                    try:
                        page.close()
                    except Exception:
                        pass

            browser.close()

        cur.close()
        conn.close()
        print("\nAutomation run completed.")

    except Exception as e:
        print(f"DB Error: {e}")


if __name__ == "__main__":
    run_automation()
