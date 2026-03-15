import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_account():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    cur.execute("SELECT dp_name, meroshare_user FROM automation_account WHERE meroshare_user = '00170441'")
    row = cur.fetchone()
    if row:
        print(f"DP Name for 00170441: {row[0]}")
    else:
        print("Account 00170441 not found in DB")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_account()
