import psycopg2
import json

db_url = "postgresql://neondb_owner:npg_PEGnh7ygJk5s@ep-quiet-rain-ain770xe-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

def query_db():
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print("\n--- ACCOUNT STATUS ---")
        cur.execute("SELECT id, meroshare_user, is_active FROM automation_account;")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        for r in rows:
            print(json.dumps(dict(zip(columns, r))))
            
        cur.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    query_db()
