#!/usr/bin/env python3
"""
Simple local server for the Email MCP Assistant
This provides a local interface to run the email automation workflow
"""

import asyncio
import json
from langgraph_flow import run_workflow
from config import EMAIL_IMAP_SERVER, EMAIL_SMTP_SERVER, EMAIL_ADDRESS, EMAIL_APP_PASSWORD
import datetime

async def run_email_workflow(max_emails: int = 10, tone: str = "polite", schedule_time: str = "2025-06-30T10:00:00Z"):
    """Run the email automation workflow with the given parameters."""
    print("🚀 Starting Email Automation Workflow...")
    print(f"📧 Max emails: {max_emails}")
    print(f"🎭 Tone: {tone}")
    print(f"⏰ Schedule time: {schedule_time}")
    print("=" * 60)
    
    try:
        # Run the LangGraph workflow
        result = await run_workflow(
            imap_server=EMAIL_IMAP_SERVER,
            smtp_server=EMAIL_SMTP_SERVER, 
            email=EMAIL_ADDRESS,
            password=EMAIL_APP_PASSWORD,
            send_time=schedule_time,
            tone=tone
        )
        
        # Display results
        print("\n📧 Email Automation Workflow Results")
        print("=" * 60)
        
        for i, email in enumerate(result, 1):
            print(f"\n📨 Email {i}:")
            print(f"   From: {email.get('from', 'Unknown')}")
            print(f"   Subject: {email.get('subject', 'No subject')}")
            print(f"   Category: {email.get('category', 'unknown')}")
            print(f"   Scheduled: {email.get('scheduled', False)}")
            print(f"   Draft: {email.get('draft', 'No draft')[:100]}...")
            print("-" * 40)
        
        print(f"\n✅ Workflow completed successfully! Processed {len(result)} emails.")
        return result
        
    except Exception as e:
        print(f"❌ Workflow Error: {str(e)}")
        return None

def main():
    """Main function to run the local server."""
    print("📧 Email MCP Assistant - Local Server")
    print("=" * 50)
    print("This server provides local access to the email automation workflow.")
    print("No API keys required - runs completely locally!")
    print()
    
    # Default parameters
    max_emails = 10
    tone = "polite"
    schedule_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)).replace(microsecond=0).isoformat()
    
    # Run the workflow
    result = asyncio.run(run_email_workflow(max_emails, tone, schedule_time))
    
    if result:
        print("\n🎉 Email automation completed successfully!")
        print("📋 Summary:")
        print(f"   • Processed {len(result)} emails")
        print(f"   • Used tone: {tone}")
        print(f"   • Scheduled for: {schedule_time}")
    else:
        print("\n❌ Email automation failed. Please check your configuration.")

if __name__ == "__main__":
    main() 