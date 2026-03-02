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
        
        print("\n--- Daily IPO Task Detail ---")
        cur.execute("SELECT name, task, enabled, last_run_at, crontab_id FROM django_celery_beat_periodictask WHERE name = 'Daily IPO Application Check';")
        columns = [desc[0] for desc in cur.description]
        task = cur.fetchone()
        if task:
            task_dict = dict(zip(columns, task))
            if task_dict['last_run_at']:
                task_dict['last_run_at'] = task_dict['last_run_at'].isoformat()
            print(json.dumps(task_dict))
        else:
            print("Task 'Daily IPO Application Check' not found!")
            
        print("\n--- Recent Logs (Last 1 hour) ---")
        cur.execute("SELECT id, account_id, company_name, status, remark, timestamp FROM automation_applicationlog WHERE timestamp > NOW() - INTERVAL '1 hour' ORDER BY timestamp DESC;")
        columns = [desc[0] for desc in cur.description]
        logs = [dict(zip(columns, row)) for row in cur.fetchall()]
        if not logs:
            print("No logs found in the last 1 hour.")
        else:
            for log in logs:
                if log['timestamp']:
                    log['timestamp'] = log['timestamp'].isoformat()
                print(json.dumps(log))
            
        cur.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    query_db()
