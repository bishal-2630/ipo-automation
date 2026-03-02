import psycopg2

db_url = "postgresql://neondb_owner:npg_PEGnh7ygJk5s@ep-quiet-rain-ain770xe-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

def check_logs():
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT id, status, remark, timestamp FROM automation_applicationlog ORDER BY id DESC LIMIT 10;")
        rows = cur.fetchall()
        if not rows:
            print("No logs found.")
        for r in rows:
            print(f"ID: {r[0]} | Status: {r[1]} | Time: {r[3]}")
            print(f"Remark: {r[2][:200]}...")
            print("-" * 20)
        cur.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_logs()
