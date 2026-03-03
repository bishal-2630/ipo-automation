"""
notifications.py
----------------
Email notification utilities for the IPO automation.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def send_email_notification(to_email, subject, message):
    """
    Sends an email notification via Gmail SMTP.
    Reads SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT from .env.
    Silently skips if credentials are missing or no recipient is given.
    """
    if not to_email:
        return

    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER") or "smtp.gmail.com"
    smtp_port = int(os.getenv("SMTP_PORT") or 587)

    if not (sender_email and sender_password):
        print("Warning: Skipping email notification (Sender credentials missing in .env)")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = f"IPO Automation <{sender_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"Email Notification Sent to {to_email}")
    except Exception as e:
        print(f"Warning: Failed to send email notification to {to_email}: {e}")


def send_push_notification(tokens, title, body):
    """
    Sends FCM Push Notification to list of tokens.
    """
    if not tokens:
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        if not firebase_admin._apps:
            # Look for config in default location
            cred_path = os.path.join(os.path.dirname(__file__), "config", "firebase_vcc.json")
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
                # Fallback: load from base64-encoded env variable (GitHub Actions)
                import base64, json
                b64 = os.environ.get("FIREBASE_CREDENTIALS_B64", "")
                if not b64:
                    print(f"Warning: Firebase credentials not found. Set FIREBASE_CREDENTIALS_B64 env var. Skipping push notification.")
                    return
                cred_json = json.loads(base64.b64decode(b64).decode())
                cred = credentials.Certificate(cred_json)
            firebase_admin.initialize_app(cred)

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
        print(f"Push Notification Sent: {response.success_count} success, {response.failure_count} failure")
        return response
    except Exception as e:
        print(f"Warning: Failed to send push notification: {e}")
