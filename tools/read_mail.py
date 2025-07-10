import imaplib
import base64
import asyncio
from typing import List, Dict
import email
from email.header import decode_header

def decode_mime_words(s):
    if not s:
        return ""
    decoded = decode_header(s)
    return ''.join(
        part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
        for part, encoding in decoded
    )

def connect_gmail_imap_xoauth2(email_address, access_token):
    """Connect to Gmail IMAP using OAuth2 access token"""
    imap = imaplib.IMAP4_SSL('imap.gmail.com')
    auth_string = f"user={email_address}\1auth=Bearer {access_token}\1\1"
    imap.authenticate('XOAUTH2', lambda x: auth_string.encode())
    return imap

async def read_inbox_emails(imap_server: str, email_address: str, access_token: str, max_emails: int = 10) -> List[Dict]:
    """
    Connects to the IMAP server and fetches the latest emails from the inbox using XOAUTH2.
    Returns a list of email metadata dicts: sender, subject, snippet.
    """
    emails = []
    loop = asyncio.get_event_loop()
    try:
        print(f"[DEBUG] Using access token for {email_address}: {access_token[:20]}... (truncated)")
        # Optionally, print the full token or its scope if available
        imap = await loop.run_in_executor(None, connect_gmail_imap_xoauth2, email_address, access_token)
        imap.select('INBOX')
        typ, data = imap.search(None, 'ALL')
        if typ != 'OK' or not data or not data[0]:
            imap.logout()
            return emails
        msg_nums = data[0].split()
        emails_to_fetch = msg_nums[-max_emails:] if len(msg_nums) > max_emails else msg_nums
        for num in reversed(emails_to_fetch):
            typ, msg_data = imap.fetch(num, '(RFC822)')
            if typ != 'OK':
                continue
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    sender = decode_mime_words(msg.get('From', ''))
                    subject = decode_mime_words(msg.get('Subject', ''))
                    date = msg.get('Date', '')
                    snippet = ''
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                payload = part.get_payload(decode=True)
                                if payload:
                                    snippet = payload[:300].decode(errors='ignore')
                                break
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            snippet = payload[:300].decode(errors='ignore')
                    emails.append({
                        'from': sender,
                        'subject': subject,
                        'date': date,
                        'snippet': snippet
                    })
        imap.logout()
    except Exception as e:
        # Log or handle error as needed
        print(f"[IMAP ERROR] {e}")
    return emails

def format_emails_for_display(emails: List[Dict]) -> str:
    """
    Formats a list of emails into a readable display string.
    """
    if not emails:
        return "📧 No emails found in inbox."
    
    result = f"📧 **Inbox ({len(emails)} emails)**\n\n"
    
    for i, email in enumerate(emails, 1):
        sender = email.get('from', 'Unknown Sender')
        subject = email.get('subject', 'No Subject')
        date = email.get('date', 'Unknown Date')
        snippet = email.get('snippet', 'No content')
        
        # Clean up the snippet
        snippet = snippet.replace('\n', ' ').replace('\r', ' ').strip()
        if len(snippet) > 150:
            snippet = snippet[:150] + "..."
        
        result += f"**{i}. {subject}**\n"
        result += f"📤 From: {sender}\n"
        result += f"📅 Date: {date}\n"
        result += f"📝 Preview: {snippet}\n"
        result += "-" * 60 + "\n\n"
    
    return result 