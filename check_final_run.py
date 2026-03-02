import psycopg2
import sys
import json

db_url = "postgresql://neondb_owner:npg_PEGnh7ygJk5s@ep-quiet-rain-ain770xe-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

def query_db():
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print("\n--- All Crontab Schedules ---")
        cur.execute("SELECT id, minute, hour, timezone FROM django_celery_beat_crontabschedule;")
        columns = [desc[0] for desc in cur.description]
        crons = [dict(zip(columns, row)) for row in cur.fetchall()]
        for c in crons:
            print(json.dumps(c))

        print("\n--- All Periodic Tasks ---")
        cur.execute("SELECT name, enabled, last_run_at, crontab_id FROM django_celery_beat_periodictask;")
        columns = [desc[0] for desc in cur.description]
        tasks = [dict(zip(columns, row)) for row in cur.fetchall()]
        for t in tasks:
            if t['last_run_at']:
                t['last_run_at'] = t['last_run_at'].isoformat()
            print(json.dumps(t))
            
        print("\n--- Last 5 Application Logs ---")
        cur.execute("SELECT status, remark, timestamp FROM automation_applicationlog ORDER BY timestamp DESC LIMIT 5;")
        for r in cur.fetchall():
            print(f"Status: {r[0]}, Remark: {r[1]}, Time: {r[2]}")
            
        cur.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    query_db()
