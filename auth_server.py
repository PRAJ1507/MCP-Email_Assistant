from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.requests import Request as StarletteRequest
import os
import json
import time
import httpx
import threading
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SESSION_SECRET_KEY

# --- Mail Scheduler Logic ---
import asyncio
import time
from apscheduler.schedulers.background import BackgroundScheduler
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

app = FastAPI(title="Email MCP Auth Server", description="OAuth authentication for Email MCP Assistant")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY, max_age=3600)

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://mail.google.com/ https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.readonly'
    },
)

USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
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

def get_current_user(request: Request):
    """Get current user from session"""
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@app.get("/")
async def home(request: Request):
    """Home page with login status"""
    user = request.session.get('user')
    if user:
        return {
            "message": "Email MCP Auth Server",
            "user": user.get('email'),
            "status": "authenticated"
        }
    return {
        "message": "Email MCP Auth Server", 
        "status": "not_authenticated",
        "login_url": "/login"
    }

@app.get("/login")
async def login(request: Request):
    """Start OAuth login flow"""
    redirect_uri = str(request.url_for('auth'))
    print(f"[DEBUG] Redirect URI: {redirect_uri}")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    """Handle OAuth callback"""
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        if "mismatching_state" in str(e):
            try:
                code = request.query_params.get('code')
                if code:
                    token_url = "https://oauth2.googleapis.com/token"
                    token_data = {
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": str(request.url_for('auth'))
                    }
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(token_url, data=token_data)
                        if resp.status_code == 200:
                            token = resp.json()
                        else:
                            return RedirectResponse(url='/')
                else:
                    return RedirectResponse(url='/')
            except Exception:
                return RedirectResponse(url='/')
        else:
            return RedirectResponse(url='/')
    except Exception:
        return RedirectResponse(url='/')
    
    user = None
    try:
        if token and "id_token" in token and token["id_token"]:
            try:
                user = await oauth.google.parse_id_token(request, token)
            except Exception:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(USERINFO_URL, headers={"Authorization": f"Bearer {token['access_token']}"})
                    user = resp.json()
        else:
            async with httpx.AsyncClient() as client:
                resp = await client.get(USERINFO_URL, headers={"Authorization": f"Bearer {token['access_token']}"})
                user = resp.json()
        
        request.session['user'] = dict(user)
        request.session['token'] = token
        
        # Save user token for MCP server
        save_user_token(
            user["email"],
            token.get("access_token"),
            token.get("refresh_token"),
            token.get("expires_at") or int(time.time()) + token.get("expires_in", 3600)
        )
        
    except Exception as e:
        print(f"Error in user processing: {e}")
        import traceback
        traceback.print_exc()
    
    return RedirectResponse(url='/')

@app.get("/logout")
async def logout(request: Request):
    """Logout user"""
    request.session.pop('user', None)
    request.session.pop('token', None)
    return RedirectResponse(url='/')

@app.get("/status")
async def status(request: Request, user: dict = Depends(get_current_user)):
    """Get authentication status"""
    return {
        "authenticated": True,
        "user": user,
        "message": "User is authenticated"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Start the mail scheduler in a background thread
    scheduler_thread = threading.Thread(target=start_mail_scheduler, daemon=True)
    scheduler_thread.start()
    print("🚀 Starting Email MCP Auth Server with Mail Scheduler")
    print("📧 Mail scheduler will run in background")
    print("🔐 Auth server will run on http://localhost:8000")
    
    uvicorn.run(app, host="localhost", port=8000) 