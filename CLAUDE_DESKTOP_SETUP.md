# Claude Desktop Integration Guide

## 🚀 Quick Setup for Claude Desktop

### 1. **Start the Combined Server (Recommended)**
```bash
uv run auth_server.py
```
This starts both the authentication server AND the mail scheduler in one process!

### 2. **Start the MCP Server**
```bash
uv run mcp_server.py
```

### 3. **Configure Claude Desktop**
1. Open Claude Desktop
2. Go to Settings → MCP Servers
3. Add a new server with these settings:
   - **Name**: Email Assistant
   - **Transport**: HTTP
   - **URL**: `http://localhost:8000` (or the port shown when you start the server)

### 4. **Authenticate with Gmail**
Before using email features, you need to authenticate:

1. **Complete OAuth Flow:**
   - Open your browser and go to: `http://localhost:8000/login`
   - Sign in with your Google account
   - Grant the necessary permissions

3. **Verify Authentication:**
   - In Claude Desktop, use the `get_authentication_status` tool
   - This will tell you if you're properly authenticated

### 5. **Use Email Features**
Once authenticated, you can use these tools:

- `get_authentication_status` - Check your auth status
- `check_user_tokens` - Debug token loading
- `run_email_automation_workflow` - Main email automation tool

## 🔧 Troubleshooting

### **"No authorized users found" Error**
This means you need to authenticate:
1. Start the combined server: `uv run auth_server.py`
2. Use the `authenticate_user` tool to get the login link
3. Complete the OAuth flow
4. Try again

### **"Token expired" Error**
Your access token has expired:
1. Start the combined server: `uv run auth_server.py`
2. Use the `authenticate_user` tool to get the login link
3. Re-authenticate to refresh your token

### **"User tokens file not found" Error**
The system can't find your authentication file:
1. Make sure you've completed the OAuth flow
2. Check that `user_tokens.json` exists in the project root
3. Use the `check_user_tokens` tool to debug

## 📧 Available Tools

### `get_authentication_status`
Check if you're authenticated and get instructions if not.

### `check_user_tokens`
Debug tool to check if the user tokens file can be loaded.

### `run_email_automation_workflow`
Main email automation tool with parameters:
- `max_emails`: Number of emails to process (default: 1)
- `tone`: Email tone - "polite", "direct", etc. (default: "polite")
- `schedule_time`: When to send emails (ISO format, default: now)

### `send_scheduled_emails`
Send all due emails immediately without waiting for background scheduler.

### `list_scheduled_emails`
View all currently scheduled emails and their status.

### `authenticate_user`
Get a direct link to authenticate with Gmail (checks if auth server is running).

### `view_inbox_emails`
View emails from your Gmail inbox with parameters:
- `max_emails`: Number of emails to retrieve (default: 10)
- `email_address`: Specific email account to use (optional)

### `list_authenticated_accounts`
List all authenticated email accounts with their status and expiration times.

## 🔄 Multi-Account Support

You can now authenticate multiple email accounts and use them interchangeably:

### Adding Multiple Accounts
1. Use `authenticate_user` multiple times with different Google accounts
2. Each account will be saved separately in `user_tokens.json`
3. Use `list_authenticated_accounts` to see all available accounts

### Using Specific Accounts
Most email tools now accept an optional `email_address` parameter:
- `view_inbox_emails(email_address="user1@gmail.com")`
- `run_email_automation_workflow(email_address="user2@gmail.com")`
- `send_scheduled_emails(email_address="user1@gmail.com")`

### Default Behavior
- If no `email_address` is specified, uses the first authenticated account
- All accounts are processed when using `send_scheduled_emails` without specifying an account

## 🎯 Example Usage

1. **Check your status:**
   ```
   Use the get_authentication_status tool
   ```

2. **Run email automation:**
   ```
   Use the run_email_automation_workflow tool with:
   - max_emails: 5
   - tone: "polite"
   - schedule_time: "2024-01-15T10:00:00Z"
   ```

3. **View inbox emails:**
   ```
   Use the view_inbox_emails tool with:
   - max_emails: 5 (or any number you want)
   - email_address: "user1@gmail.com" (optional, for specific account)
   ```

4. **Send scheduled emails:**
   ```
   Use the send_scheduled_emails tool with:
   - email_address: "user1@gmail.com" (optional, for specific account)
   ```

5. **Check scheduled emails:**
   ```
   Use the list_scheduled_emails tool
   ```

6. **List all accounts:**
   ```
   Use the list_authenticated_accounts tool to see all available accounts
   ```

7. **Multi-account workflow:**
   ```
   - Check accounts: list_authenticated_accounts
   - View inbox for account 1: view_inbox_emails(email_address="user1@gmail.com")
   - View inbox for account 2: view_inbox_emails(email_address="user2@gmail.com")
   - Run automation for account 1: run_email_automation_workflow(email_address="user1@gmail.com")
   ```

## 🔒 Security Notes

- Your Gmail tokens are stored locally in `user_tokens.json`
- Never share this file or commit it to version control
- Tokens expire automatically and need to be refreshed
- The auth server runs locally and doesn't expose your credentials

## 🆘 Getting Help

If you encounter issues:

1. **Check authentication status** using the `get_authentication_status` tool
2. **Debug token loading** using the `check_user_tokens` tool
3. **Check the console output** from the MCP server for error messages
4. **Verify file paths** by running `python test_paths.py` 