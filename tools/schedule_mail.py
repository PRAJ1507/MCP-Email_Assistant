from typing import Dict, List
import datetime
import re
import json
import os
import smtplib
from email.mime.text import MIMEText
import base64
import time
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from tools.scheduler_utils import load_all_users, refresh_access_token

SCHEDULED_MAIL_FILE = os.path.join(os.path.dirname(__file__), "scheduled_emails.json")

def extract_sender_name(sender: str) -> str:
    """
    Extracts the sender's name from the email address.
    Examples:
    - "John Doe <john@example.com>" -> "John"
    - "john@example.com" -> "John"
    - "John Doe" -> "John"
    """
    if not sender:
        return "Unknown Sender"
    
    # Remove email address if present
    sender_clean = re.sub(r'<[^>]+>', '', sender).strip()
    
    # If it's just an email address, extract the name part
    if '@' in sender_clean and ' ' not in sender_clean:
        name_part = sender_clean.split('@')[0]
        # Capitalize first letter
        return name_part.capitalize()
    
    # If it's a full name, take the first name
    if ' ' in sender_clean:
        first_name = sender_clean.split(' ')[0]
        return first_name
    
    # If it's a single word, use it as is
    return sender_clean

def load_scheduled_emails() -> List[Dict]:
    if not os.path.exists(SCHEDULED_MAIL_FILE):
        return []
    with open(SCHEDULED_MAIL_FILE, "r") as f:
        return json.load(f)

def save_scheduled_emails(emails: List[Dict]):
    with open(SCHEDULED_MAIL_FILE, "w") as f:
        json.dump(emails, f, indent=2, default=str)

def is_duplicate_email(email: Dict, send_time: str) -> bool:
    emails = load_scheduled_emails()
    for scheduled in emails:
        if (
            scheduled.get('from') == email.get('from') and
            scheduled.get('subject') == email.get('subject')
        ):
            return True
    return False

def schedule_email_send(email: Dict, send_time: str) -> bool:
    """
    Schedules the given email to be sent at the specified time.
    Persists the scheduled email in a JSON file.
    Returns True if scheduled successfully, False if duplicate.
    """
    if is_duplicate_email(email, send_time):
        print(f"[SKIP] Duplicate email not scheduled: {email.get('subject')} from {email.get('from')}")
        return False
    emails = load_scheduled_emails()
    # Assign a unique id
    email_id = len(emails) + 1
    scheduled_email = {
        "id": email_id,
        "to": email.get("to"),
        "from": email.get("from"),
        "subject": email.get("subject"),
        "body": email.get("draft"),
        "scheduled_time": send_time,
        "sent": False
    }
    emails.append(scheduled_email)
    save_scheduled_emails(emails)
    print(f"[SCHEDULE] Email to: {scheduled_email['to']} at {send_time}")
    return True

def get_due_emails() -> List[Dict]:
    """
    Returns a list of emails whose scheduled time is <= now and not sent.
    """
    emails = load_scheduled_emails()
    now = datetime.datetime.now(datetime.timezone.utc)
    due = []
    for email in emails:
        if not email["sent"]:
            scheduled_time = datetime.datetime.fromisoformat(email["scheduled_time"])
            if scheduled_time <= now:
                due.append(email)
    return due

def mark_email_sent(email_id: int):
    emails = load_scheduled_emails()
    for email in emails:
        if email["id"] == email_id:
            email["sent"] = True
    save_scheduled_emails(emails)

def connect_gmail_smtp_xoauth2(email_address, access_token):
    """Connect to Gmail SMTP using OAuth2 access token"""
    auth_string = f"user={email_address}\1auth=Bearer {access_token}\1\1"
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.docmd('AUTH', 'XOAUTH2 ' + base64.b64encode(auth_string.encode()).decode())
    return smtp

def send_email(smtp_server: str, email_address: str, access_token: str, to: str, subject: str, body: str):
    print(f"[DEBUG] send_email called: from={email_address}, to={to}")
    print(f"[DEBUG] Using token: {access_token[:20]}...")
    
    # Create email message exactly like the working test
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = to
    
    # Extract email address exactly like the working test
    to_email = to
    if '<' in to_email and '>' in to_email:
        to_email = to_email.split('<')[1].split('>')[0]
    
    print(f"[DEBUG] Email headers - From: {msg['From']}, To: {msg['To']}")
    print(f"[DEBUG] Sending to email address: {to_email}")
    
    # Use the exact same connection pattern as the working test
    print(f"[DEBUG] Connecting to SMTP...")
    smtp = connect_gmail_smtp_xoauth2(email_address, access_token)
    print(f"[DEBUG] SMTP connected successfully!")
    
    try:
        print(f"[DEBUG] Sending email...")
        smtp.sendmail(email_address, [to_email], msg.as_string())
        print(f"[DEBUG] Email sent successfully!")
    except Exception as e:
        print(f"[DEBUG] Sendmail failed: {e}")
        print(f"[DEBUG] Error type: {type(e).__name__}")
        raise e
    finally:
        print(f"[DEBUG] Closing SMTP connection...")
        smtp.quit()
        print(f"[DEBUG] SMTP connection closed")

def process_due_emails(smtp_server: str, email_address: str, access_token: str):
    print(f"[DEBUG] process_due_emails called for {email_address} with token: {access_token[:20]}...")
    due_emails = get_due_emails()
    print(f"[DEBUG] Found {len(due_emails)} due emails")
    for email in due_emails:
        print(f"[DEBUG] Checking email {email['id']}: from={email.get('from')}, to={email['to']}")
        # Only send emails that were created by this user
        if email.get("from") == email_address:
            print(f"[DEBUG] Sending email {email['id']} from {email_address} to {email['to']}")
            try:
                send_email(
                    smtp_server=smtp_server,
                    email_address=email_address,
                    access_token=access_token,
                    to=email["to"],
                    subject=email["subject"],
                    body=email["body"]
                )
                mark_email_sent(email["id"])
                print(f"[SENT] Email to: {email['to']} (ID: {email['id']}) from {email_address}")
                # Add a small delay between emails to avoid rate limiting
                time.sleep(2)
            except Exception as e:
                print(f"[ERROR] Failed to send scheduled email to {email['to']} from {email_address}: {e}")
                print(f"[DEBUG] Error details: {type(e).__name__}: {str(e)}")
        else:
            print(f"[SKIP] Email {email['id']} not sent - belongs to {email.get('from')}, not {email_address}")

async def send_due_emails_immediately() -> str:
    """
    Immediately send all due emails without relying on background scheduler.
    Returns a status message about what was sent.
    """
    try:
        users = load_all_users()
        if not users:
            return "❌ No authenticated users found. Please authenticate first."
        
        total_sent = 0
        status_messages = []
        
        for user in users:
            email = user["email"]
            access_token = user["access_token"]
            expires_at = user.get("expires_at", 0)
            current_time = int(time.time())
            
            # Check if token is expired
            if current_time >= expires_at:
                print(f"[DEBUG] Token expired for {email}, refreshing...")
                access_token, _ = await refresh_access_token(user)
            
            # Get due emails for this user
            due_emails = get_due_emails()
            user_due_emails = [email for email in due_emails if email.get("from") == email]
            
            if not user_due_emails:
                status_messages.append(f"📧 {email}: No due emails")
                continue
            
            # Send due emails for this user
            sent_count = 0
            for email_data in user_due_emails:
                try:
                    send_email(
                        smtp_server="smtp.gmail.com",
                        email_address=email,
                        access_token=access_token,
                        to=email_data["to"],
                        subject=email_data["subject"],
                        body=email_data["body"]
                    )
                    mark_email_sent(email_data["id"])
                    sent_count += 1
                    total_sent += 1
                    time.sleep(1)  # Small delay between emails
                except Exception as e:
                    status_messages.append(f"❌ {email}: Failed to send email to {email_data['to']}: {str(e)}")
            
            if sent_count > 0:
                status_messages.append(f"✅ {email}: Sent {sent_count} emails")
        
        if total_sent == 0:
            return "📧 No due emails to send at this time."
        else:
            return f"🎉 Successfully sent {total_sent} emails!\n\n" + "\n".join(status_messages)
            
    except Exception as e:
        return f"❌ Error sending due emails: {str(e)}" 