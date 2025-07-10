#!/usr/bin/env python3
"""
Standalone mail scheduler that runs continuously
"""
import asyncio
import time
import sys
import os
from apscheduler.schedulers.background import BackgroundScheduler

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.scheduler_utils import load_all_users, refresh_access_token
from tools.schedule_mail import process_due_emails

def start_mail_scheduler():
    scheduler = BackgroundScheduler()
    async def process_all_users():
        users = load_all_users()
        for user in users:
            now = int(time.time())
            access_token = user["access_token"]
            expires_at = user.get("expires_at", 0)
            if now >= expires_at:
                print(f"[SCHEDULER] Refreshing token for {user['email']}")
                access_token, _ = await refresh_access_token(user)
            try:
                print(f"[SCHEDULER] Processing emails for {user['email']} with token: {access_token[:20]}...")
                process_due_emails("smtp.gmail.com", user["email"], access_token)
            except Exception as e:
                print(f"[SCHEDULER ERROR] {user['email']}: {e}")
    def run_async():
        asyncio.run(process_all_users())
    scheduler.add_job(
        run_async,
        'interval',
        minutes=1,
        id='mail_scheduler'
    )
    scheduler.start()
    print("[SCHEDULER] Mail scheduler started (runs every minute)")

def main():
    print("🚀 Starting standalone mail scheduler...")
    print("📧 Scheduler will check for due emails every minute")
    print("⏰ Press Ctrl+C to stop the scheduler")
    
    # Start the scheduler
    start_mail_scheduler()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping mail scheduler...")
        sys.exit(0)

if __name__ == "__main__":
    main() 