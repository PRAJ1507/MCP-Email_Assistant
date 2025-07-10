#this is a dev file for testing the work flow.
# use the email app password to set your mail address
import asyncio
from config import EMAIL_IMAP_SERVER, EMAIL_SMTP_SERVER, EMAIL_ADDRESS,EMAIL_APP_PASSWORD
from langgraph_flow import run_workflow
import datetime

if __name__ == "__main__":
    # Set your test parameters
    send_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)).replace(microsecond=0).isoformat()
    tone = "polite"  # or "direct"

    print("Running email automation workflow...")
    result = asyncio.run(
        run_workflow(
            EMAIL_IMAP_SERVER,
            EMAIL_SMTP_SERVER,
            EMAIL_ADDRESS,# specify your email id and passwordin .env file and get it from the config.py
            EMAIL_APP_PASSWORD,
            send_time=send_time,
            tone=tone
        )
    )
    print("\nWorkflow result:")
    for mail in result:
        print("-" * 40)
        print(f"From: {mail.get('from')}")
        print(f"Subject: {mail.get('subject')}")
        print(f"Category: {mail.get('category')}")
        print(f"Draft: {mail.get('draft')}")
        print(f"Scheduled: {mail.get('scheduled', False)}") 