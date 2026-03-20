import os
import sys
from dotenv import load_dotenv

# Add the current directory to path so it can import notifications
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from notifications import send_email_notification, broadcast_push_notification

load_dotenv()

def test_notification():
    test_email = os.getenv("SENDER_EMAIL") or "test@example.com"
    subject = "Test: IPO Allotted Notification"
    message = "🎉 Congratulations! This is a test notification for IPO Allotment."
    
    print("Testing Email Notification...")
    send_email_notification(test_email, subject, message)
    
    print("\nTesting Push Notification...")
    broadcast_push_notification("IPO Allotted Test", message)

if __name__ == "__main__":
    test_notification()
