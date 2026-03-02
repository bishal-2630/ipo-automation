import psycopg2

db_url = "postgresql://neondb_owner:npg_PEGnh7ygJk5s@ep-quiet-rain-ain770xe-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

def check_count():
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM automation_applicationlog;")
        count = cur.fetchone()[0]
        print(f"Total Logs in ApplicationLog: {count}")
        
        if count > 0:
            cur.execute("SELECT status, remark, timestamp FROM automation_applicationlog ORDER BY timestamp DESC LIMIT 5;")
            for r in cur.fetchall():
                print(f"[{r[2]}] {r[0]}: {r[1]}")
            
        cur.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_count()
