import os
import json
import time
import httpx
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

# Define the absolute path to user_tokens.json
USER_TOKENS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_tokens.json")

# Load all users

def load_all_users():
    print(f"[DEBUG] load_all_users: USER_TOKENS_FILE = {USER_TOKENS_FILE}")
    print(f"[DEBUG] load_all_users: File exists = {os.path.exists(USER_TOKENS_FILE)}")
    if os.path.exists(USER_TOKENS_FILE):
        with open(USER_TOKENS_FILE, "r") as f:
            users = json.load(f)
            print(f"[DEBUG] load_all_users: Loaded {len(users)} users")
            return users
    print(f"[DEBUG] load_all_users: No users found")
    return []

# Refresh access token if expired
async def refresh_access_token(user):
    if not user.get("refresh_token"):
        return user["access_token"], user["expires_at"]
    token = {
        "refresh_token": user["refresh_token"]
    }
    from mcp_server import oauth  # Delayed import to avoid circular import at module level
    new_token = await oauth.google.refresh_token(
        url="https://oauth2.googleapis.com/token",
        refresh_token=token["refresh_token"],
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )
    user["access_token"] = new_token["access_token"]
    user["expires_at"] = int(time.time()) + new_token.get("expires_in", 3600)
    # Save user token (delayed import)
    from mcp_server import save_user_token
    save_user_token(user["email"], user["access_token"], user["refresh_token"], user["expires_at"])
    return user["access_token"], user["expires_at"] 