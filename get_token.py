import psycopg2
import json

db_url = "postgresql://neondb_owner:npg_PEGnh7ygJk5s@ep-quiet-rain-ain770xe-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

def get_token():
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Get the first token in the database
        cur.execute("SELECT key, user_id FROM authtoken_token LIMIT 1;")
        row = cur.fetchone()
        if row:
            print(f"Token: {row[0]}")
        else:
            print("No token found in database!")
            
        cur.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    get_token()
