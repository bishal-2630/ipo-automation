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
