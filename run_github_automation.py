import os
import psycopg2
import json
from playwright.sync_api import sync_playwright
from main import login, apply_ipo
import datetime

# Database connection
DB_URL = os.environ.get("DATABASE_URL")

def run_automation():
    if not DB_URL:
        print("Error: DATABASE_URL not set.")
        return

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # 1. Fetch active accounts
        cur.execute("SELECT id, meroshare_user, meroshare_pass, dp_name, crn, tpin, bank_name, kitta, owner_id FROM automation_account WHERE is_active = True;")
        columns = [desc[0] for desc in cur.description]
        accounts = [dict(zip(columns, row)) for row in cur.fetchall()]

        if not accounts:
            print("No active accounts found.")
            return

        print(f"Found {len(accounts)} active accounts. Starting automation...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            for acc in accounts:
                print(f"Processing account: {acc['meroshare_user']}")
                page = browser.new_page()
                
                try:
                    # Map to the format expected by main.py
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
                    login_result = login(page, account_data['MEROSHARE_USER'], account_data['MEROSHARE_PASS'], account_data['DP_NAME'])
                    
                    if login_result is True:
                        print(f"Login successful for {acc['meroshare_user']}. Applying IPO...")
                        apply_ipo(page, account_data)
                        status = "Success"
                        remark = "IPO applied successfully via GitHub Action"
                    else:
                        print(f"Login failed for {acc['meroshare_user']}: {login_result}")
                        status = "Failed"
                        remark = f"Login failed: {login_result}"

                except Exception as e:
                    print(f"Error processing {acc['meroshare_user']}: {e}")
                    status = "Error"
                    remark = str(e)
                finally:
                    # 2. Log result back to DB
                    cur.execute("""
                        INSERT INTO automation_applicationlog (account_id, company_name, status, remark, timestamp)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (acc['id'], "Auto-Check", status, remark, datetime.datetime.now()))
                    conn.commit()
                    page.close()

            browser.close()

        cur.close()
        conn.close()
        print("Automation run completed.")

    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    run_automation()
