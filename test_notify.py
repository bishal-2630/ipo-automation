import os
import sys
from dotenv import load_dotenv

# Add the current directory to path so it can import notifications
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from notifications import send_email_notification, broadcast_push_notification

load_dotenv()

def test_notification():
    test_email = os.getenv("SENDER_EMAIL") or "test@example.com"
    subject = "[MeroShare] Success: Test Company"
    
    # Real format from main.py line 1439
    username = "TestUser"
    company_name = "Api Power Company Ltd."
    kitta = "10"
    message = f"Congratulations!! {company_name} IPO has been allotted successfully ({kitta} Kitta)."
    
    print("Testing Email Notification...")
    send_email_notification(test_email, subject, f"Hi {username},\n\n{message}")
    
    print("\nTesting Push Notification...")
    # Real format from main.py line 1451 uses username as title
    broadcast_push_notification(username, message)

if __name__ == "__main__":
    test_notification()
