import psycopg2
import json

db_url = "postgresql://neondb_owner:npg_PEGnh7ygJk5s@ep-quiet-rain-ain770xe-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

def query_db():
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print("\n--- LATEST 20 APPLICATION LOGS ---")
        cur.execute("""
            SELECT l.id, a.meroshare_user, l.company_name, l.status, l.remark, l.timestamp 
            FROM automation_applicationlog l
            JOIN automation_account a ON l.account_id = a.id
            ORDER BY l.timestamp DESC 
            LIMIT 20;
        """)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        if not rows:
            print("No logs found in ApplicationLog table.")
        for r in rows:
            log_dict = dict(zip(columns, r))
            if log_dict['timestamp']:
                log_dict['timestamp'] = log_dict['timestamp'].isoformat()
            print(json.dumps(log_dict))
            
        cur.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    query_db()
