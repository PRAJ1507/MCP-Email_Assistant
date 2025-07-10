from mcp.server.fastmcp import FastMCP
from langgraph_flow import run_workflow
from tools.scheduler_utils import load_all_users, refresh_access_token
from tools.schedule_mail import send_due_emails_immediately
from tools.read_mail import read_inbox_emails, format_emails_for_display
import datetime
import os
import json
import time

mcp = FastMCP("Email Assistant MCP")

# Define the absolute path to user_tokens.json
USER_TOKENS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_tokens.json")



def save_user_token(email, access_token, refresh_token, expires_at):
    """Save or update user token info"""
    if os.path.exists(USER_TOKENS_FILE):
        with open(USER_TOKENS_FILE, "r") as f:
            users = json.load(f)
    else:
        users = []
    
    found = False
    for user in users:
        if user["email"] == email:
            user["access_token"] = access_token
            user["refresh_token"] = refresh_token
            user["expires_at"] = expires_at
            found = True
            break
    
    if not found:
        users.append({
            "email": email,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at
        })
    
    with open(USER_TOKENS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_access_token_for_email(email: str) -> str:
    users = load_all_users()
    print(f"[DEBUG] Looking for email: {email}")
    print(f"[DEBUG] Available users: {[user['email'] for user in users]}")
    for user in users:
        if user["email"] == email:
            print(f"[DEBUG] Found token for {email}")
            return user["access_token"]
    print(f"[DEBUG] No token found for {email}")
    return None

@mcp.tool()
async def check_user_tokens() -> str:
    """Check if user tokens file exists and can be loaded"""
    try:
        print(f"[DEBUG] USER_TOKENS_FILE path: {USER_TOKENS_FILE}")
        print(f"[DEBUG] File exists: {os.path.exists(USER_TOKENS_FILE)}")
        print(f"[DEBUG] Current working directory: {os.getcwd()}")
        
        if os.path.exists(USER_TOKENS_FILE):
            with open(USER_TOKENS_FILE, "r") as f:
                users = json.load(f)
            return f"✅ User tokens file found! {len(users)} users loaded. Users: {[user['email'] for user in users]}"
        else:
            return f"❌ User tokens file not found at: {USER_TOKENS_FILE}"
    except Exception as e:
        return f"❌ Error checking user tokens: {str(e)}"

@mcp.tool()
async def list_authenticated_accounts() -> str:
    """List all authenticated email accounts with their status"""
    try:
        users = load_all_users()
        if not users:
            return "❌ No authenticated accounts found."
        
        result = f"📧 **{len(users)} Authenticated Account(s):**\n\n"
        current_time = int(time.time())
        
        for i, user in enumerate(users, 1):
            email = user.get('email', 'Unknown')
            expires_at = user.get('expires_at', 0)
            status = "✅ Active" if current_time < expires_at else "⚠️ Expired"
            
            result += f"**{i}. {email}**\n"
            result += f"   Status: {status}\n"
            if current_time < expires_at:
                result += f"   Expires: {datetime.datetime.fromtimestamp(expires_at)}\n"
                result += f"   Remaining: {expires_at - current_time} seconds\n"
            else:
                result += f"   ⚠️ Token expired - needs re-authentication\n"
            result += "\n"
        
        result += "💡 **Usage:**\n"
        result += "- Use `view_inbox_emails` with `email_address` parameter\n"
        result += "- Use `run_email_automation_workflow` with `email_address` parameter\n"
        result += "- Use `send_scheduled_emails` with `email_address` parameter\n"
        
        return result
    except Exception as e:
        return f"❌ Error listing accounts: {str(e)}"

@mcp.tool()
async def get_authentication_status() -> str:
    """Get the current authentication status and provide instructions if needed"""
    try:
        users = load_all_users()
        if not users:
            return """❌ No authenticated users found!

🔐 To authenticate:
1. Start the auth server: `uv run auth_server.py`
2. Use the `authenticate_user` tool to get the login link
3. Complete the Google OAuth flow
4. Return here and try again

The auth server will save your tokens for the MCP server to use."""
        
        if len(users) == 1:
            user = users[0]
            email = user.get('email', 'Unknown')
            expires_at = user.get('expires_at', 0)
            current_time = int(time.time())
            
            if current_time >= expires_at:
                return f"""⚠️ Token expired for {email}!

🔄 Your access token has expired. Please:
1. Start the auth server: `uv run auth_server.py`
2. Use the `authenticate_user` tool to get the login link
3. Re-authenticate to refresh your token
4. Return here and try again"""
            
            return f"""✅ Authenticated as {email}

🎉 You're ready to use email automation!
- Token expires at: {datetime.datetime.fromtimestamp(expires_at)}
- Time remaining: {expires_at - current_time} seconds

You can now use the `run_email_automation_workflow` tool."""
        else:
            # Multiple users
            result = f"✅ **{len(users)} accounts authenticated:**\n\n"
            current_time = int(time.time())
            
            for i, user in enumerate(users, 1):
                email = user.get('email', 'Unknown')
                expires_at = user.get('expires_at', 0)
                status = "✅ Active" if current_time < expires_at else "⚠️ Expired"
                
                result += f"**{i}. {email}** - {status}\n"
                if current_time < expires_at:
                    result += f"   Token expires: {datetime.datetime.fromtimestamp(expires_at)}\n"
                    result += f"   Time remaining: {expires_at - current_time} seconds\n"
                else:
                    result += f"   ⚠️ Needs re-authentication\n"
                result += "\n"
            
            result += "💡 Use `list_authenticated_accounts` to see all accounts or specify an email in other tools."
            return result
        
    except Exception as e:
        return f"❌ Error checking authentication: {str(e)}"

@mcp.tool()
async def authenticate_user() -> str:
    """Get the authentication URL and instructions for logging in"""
    try:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get("http://localhost:8000/")
                if response.status_code == 200:
                    auth_url = "http://localhost:8000/login"
                    return f"""🔐 **Authentication Ready!**\n\n✅ Auth server is running at http://localhost:8000\n\n**Click here to authenticate:**\n🔗 **{auth_url}**\n\n**Steps:**\n1. Click the link above (or copy and paste it into your browser)\n2. Sign in with your Google account\n3. Grant the necessary permissions\n4. Return here and use `get_authentication_status` to verify\n\n**What this does:**\n- Connects your Gmail account securely\n- Allows the email assistant to read and send emails\n- Stores tokens locally for future use\n\n**Security:** Your credentials are never stored - only secure access tokens are saved locally."""
                else:
                    return """❌ **Auth server not responding properly**\n\nThe auth server is running but not responding correctly. Please:\n1. Stop the auth server (Ctrl+C)\n2. Restart it: `uv run auth_server.py`\n3. Try this tool again"""
        except httpx.ConnectError:
            return """❌ **Auth server not running**\n\nThe authentication server is not running. Please:\n\n1. **Start the auth server:**\n   ```bash\n   uv run auth_server.py\n   ```\n\n2. **Wait for it to start** (you'll see \"Uvicorn running on http://localhost:8000\")\n\n3. **Use this tool again** to get the login link\n\n**What the auth server does:**\n- Handles Google OAuth authentication\n- Securely stores your access tokens\n- Enables email automation features\n\nOnce the auth server is running, this tool will provide you with a direct login link."""
        except Exception as e:
            return f"""❌ **Error checking auth server: {str(e)}**\n\nPlease ensure the auth server is running:\n```bash\nuv run auth_server.py\n```"""
    except Exception as e:
        return f"❌ Error with authentication tool: {str(e)}"

@mcp.tool()
async def run_email_automation_workflow(
    max_emails: int = 1,
    tone: str = "polite",
    schedule_time: str = str((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=0)).replace(microsecond=0).isoformat()),
    email_address: str = None
) -> str:
    # Get the authorized email
    print(f"[DEBUG] USER_TOKENS_FILE path: {USER_TOKENS_FILE}")
    print(f"[DEBUG] File exists: {os.path.exists(USER_TOKENS_FILE)}")
    
    try:
        users = load_all_users()
        if not users:
            return """❌ No authorized users found!

🔐 Please authenticate first:
1. Start the auth server: `uv run auth_server.py`
2. Use the `authenticate_user` tool to get the login link
3. Complete the Google OAuth flow
4. Return here and try again

You can also use the `get_authentication_status` tool to check your current status."""
        
        # Find the user to use
        user = None
        if email_address:
            # Find specific user by email
            for u in users:
                if u.get('email') == email_address:
                    user = u
                    break
            if not user:
                available_emails = [u.get('email') for u in users]
                return f"""❌ Email address '{email_address}' not found!

Available accounts: {', '.join(available_emails)}

Use `list_authenticated_accounts` to see all available accounts."""
        else:
            # Use first user if no email specified
            user = users[0]
        
        email = user.get('email', 'Unknown')
        access_token = user.get('access_token')
        expires_at = user.get('expires_at', 0)
        current_time = int(time.time())
        
        if current_time >= expires_at:
            return f"""⚠️ Token expired for {email}!

🔄 Your access token has expired. Please:
1. Start the auth server: `uv run auth_server.py`
2. Use the `authenticate_user` tool to get the login link
3. Re-authenticate to refresh your token
4. Return here and try again"""
        
        if not access_token:
            return f"""❌ No access token found for {email}!

🔐 Please re-authenticate:
1. Start the auth server: `uv run auth_server.py`
2. Use the `authenticate_user` tool to get the login link
3. Complete the Google OAuth flow
4. Return here and try again"""
        
        print(f"[DEBUG] Using authorized email: {email}")
        print(f"[DEBUG] Token expires at: {datetime.datetime.fromtimestamp(expires_at)}")
        
    except Exception as e:
        return f"❌ Error loading user authentication: {str(e)}"
    
    try:
        result = await run_workflow(
            imap_server="imap.gmail.com",
            smtp_server="smtp.gmail.com",
            email=email,
            access_token=access_token,
            send_time=schedule_time,
            tone=tone,
            max_emails=max_emails
        )
        result_text = "📧 Email Automation Workflow Results\n"
        result_text += "=" * 50 + "\n\n"
        for email in result:
            result_text += f"From: {email.get('from', 'Unknown')}\n"
            result_text += f"Subject: {email.get('subject', 'No subject')}\n"
            result_text += f"Category: {email.get('category', 'unknown')}\n"
            result_text += f"Scheduled: {email.get('scheduled', False)}\n"
            result_text += f"Draft: {email.get('draft', 'No draft')[:200]}...\n"
            result_text += "-" * 50 + "\n\n"
        return result_text
    except Exception as e:
        return f"❌ Workflow Error: {str(e)}"

@mcp.tool()
async def send_scheduled_emails(email_address: str = None) -> str:
    """Send all due emails immediately without waiting for background scheduler"""
    try:
        if email_address:
            # Check if the email address exists
            users = load_all_users()
            user_found = False
            for user in users:
                if user.get('email') == email_address:
                    user_found = True
                    break
            
            if not user_found:
                available_emails = [u.get('email') for u in users]
                return f"""❌ Email address '{email_address}' not found!

Available accounts: {', '.join(available_emails)}

Use `list_authenticated_accounts` to see all available accounts."""
        
        return await send_due_emails_immediately()
    except Exception as e:
        return f"❌ Error sending scheduled emails: {str(e)}"

@mcp.tool()
async def list_scheduled_emails() -> str:
    """List all currently scheduled emails"""
    try:
        from tools.schedule_mail import load_scheduled_emails, get_due_emails
        emails = load_scheduled_emails()
        due_emails = get_due_emails()
        
        if not emails:
            return "📧 No scheduled emails found."
        
        result = f"📧 Found {len(emails)} scheduled emails:\n\n"
        
        for email in emails:
            status = "✅ SENT" if email.get("sent", False) else "⏰ PENDING"
            if email in due_emails:
                status = "🚀 DUE NOW"
            
            result += f"ID: {email.get('id')} | {status}\n"
            result += f"To: {email.get('to', 'Unknown')}\n"
            result += f"From: {email.get('from', 'Unknown')}\n"
            result += f"Subject: {email.get('subject', 'No subject')}\n"
            result += f"Scheduled: {email.get('scheduled_time', 'Unknown')}\n"
            result += f"Body: {email.get('body', 'No body')[:100]}...\n"
            result += "-" * 50 + "\n\n"
        
        return result
    except Exception as e:
        return f"❌ Error listing scheduled emails: {str(e)}"

@mcp.tool()
async def view_inbox_emails(max_emails: int = 10, email_address: str = None) -> str:
    """View emails from your Gmail inbox"""
    try:
        users = load_all_users()
        if not users:
            return """❌ No authenticated users found!

🔐 Please authenticate first:
1. Start the auth server: `uv run auth_server.py`
2. Use the `authenticate_user` tool to get the login link
3. Complete the Google OAuth flow
4. Return here and try again"""
        
        # Find the user to use
        user = None
        if email_address:
            # Find specific user by email
            for u in users:
                if u.get('email') == email_address:
                    user = u
                    break
            if not user:
                available_emails = [u.get('email') for u in users]
                return f"""❌ Email address '{email_address}' not found!

Available accounts: {', '.join(available_emails)}

Use `list_authenticated_accounts` to see all available accounts."""
        else:
            # Use first user if no email specified
            user = users[0]
        
        email = user.get('email', 'Unknown')
        access_token = user.get('access_token')
        expires_at = user.get('expires_at', 0)
        current_time = int(time.time())
        
        if current_time >= expires_at:
            return f"""⚠️ Token expired for {email}!

🔄 Your access token has expired. Please:
1. Start the auth server: `uv run auth_server.py`
2. Use the `authenticate_user` tool to get the login link
3. Re-authenticate to refresh your token
4. Return here and try again"""
        
        if not access_token:
            return f"""❌ No access token found for {email}!

🔐 Please re-authenticate:
1. Start the auth server: `uv run auth_server.py`
2. Use the `authenticate_user` tool to get the login link
3. Complete the Google OAuth flow
4. Return here and try again"""
        
        print(f"[DEBUG] Reading emails for: {email}")
        
        # Read emails from inbox
        emails = await read_inbox_emails(
            imap_server="imap.gmail.com",
            email_address=email,
            access_token=access_token,
            max_emails=max_emails
        )
        
        # Format and return the emails
        result = format_emails_for_display(emails)
        if email_address:
            result = f"📧 **Inbox for {email}**\n\n" + result
        return result
        
    except Exception as e:
        return f"❌ Error reading emails: {str(e)}"

if __name__ == "__main__":
    print("🚀 Starting Email MCP Server")
    print("📧 Mail scheduler is now handled by the auth server")
    print("💡 Start the auth server with: uv run auth_server.py")
    
    # Run the MCP server
    mcp.run(transport="streamable-http") 