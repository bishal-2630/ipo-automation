import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def check_db():
    if not DB_URL:
        print("Error: DATABASE_URL not set.")
        return

    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("--- Accounts ---")
        cur.execute("SELECT id, meroshare_user FROM automation_account")
        for row in cur.fetchall():
            print(f"ID: {row[0]}, User: {row[1]}")
            
        print("\n--- Recent Application Logs (Last 5) ---")
        cur.execute("SELECT id, account_id, company_name, status, remark, timestamp FROM automation_applicationlog ORDER BY timestamp DESC LIMIT 5")
        for row in cur.fetchall():
            print(f"ID: {row[0]}, Acc: {row[1]}, Company: {row[2]}, Status: {row[3]}, Remark: {row[4]}, Time: {row[5]}")

        print("\n--- Recent OTPs (Last 5) ---")
        cur.execute("SELECT id, account_id, otp_code, is_used, created_at FROM automation_bankotp ORDER BY created_at DESC LIMIT 5")
        for row in cur.fetchall():
            print(f"ID: {row[0]}, Acc: {row[1]}, Code: {row[2]}, Used: {row[3]}, Time: {row[4]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    check_db()
