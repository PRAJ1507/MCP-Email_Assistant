# MCP-Email-Assistant

# Email MCP Assistant

A **LangGraph + MCP hybrid** email automation assistant that combines the power of LangGraph workflow orchestration with the Model Context Protocol (MCP) for seamless AI integration.

## 🏗️ Architecture

This project implements a **hybrid architecture**:

- **LangGraph**: Orchestrates the email workflow as a graph (read → categorize → draft → schedule)
- **MCP**: Exposes the complete LangGraph workflow as a single tool that can be called by MCP clients
- **Hybrid**: Combines both for powerful, protocol-based email automation

## 🔧 Features

- **LangGraph Workflow**: Automated email processing pipeline
  - Read inbox emails from Gmail
  - Categorize emails by priority using AI (Ollama LLM)
  - Draft personalized responses using AI
  - Schedule emails for later sending
- **MCP Integration**: Single tool exposure for AI assistants
  - Complete workflow as one MCP tool
  - Configurable parameters (max emails, tone, schedule time)
  - Protocol-based integration
- **Local AI**: Uses Ollama for privacy and performance
- **Smart Name Extraction**: Automatically extracts sender names for personalized responses

## 🚀 Quick Start

1. **Install [uv](https://github.com/astral-sh/uv) (ultra-fast Python package manager):**
   ```bash
   pip install uv
   ```

2. **Install dependencies:**
   ```bash
   uv init .
   uv add -r requirements.txt
   ```

3. **Configure environment** (create `.env` file):
   ```env
   EMAIL_IMAP_SERVER=imap.gmail.com
   EMAIL_SMTP_SERVER=smtp.gmail.com
   EMAIL_ADDRESS=your-email@gmail.com (for testing)
   EMAIL_PASSWORD=your-app-password (for testing)
   GOOGLE_CLIENT_ID=your-google-oauth-client-id
   GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
   SESSION_SECRET_KEY=your-random-session-secret-key
   ```

4. **Start Ollama** (for local LLM):
   ```bash
   ollama serve
   ollama pull llama3.2
   ```

5. **Start the server:**
   ```bash
   start_services.bat
   ```

6. **Test the workflow:**
   ```bash
   uv run main.py
   ```

7. **(Optional) Start FastMCP MCP server manually:**
   ```bash
   uv run uvicorn mcp_server:app --reload
   ```

## ⚙️ Environment Setup

Before running the project, you must create a `.env` file in the project root with the following variables:

```env
# Gmail IMAP/SMTP servers
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_SMTP_SERVER=smtp.gmail.com

# Google OAuth2 credentials (required for Gmail API access)
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret

# Session secret key (for FastAPI session security)
SESSION_SECRET_KEY=your-random-session-secret-key

# (Optional, for legacy direct login/testing only)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password-or-access-token
```

### How to get Google OAuth2 credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Create a new OAuth 2.0 Client ID (type: Web application).
3. Set the redirect URI to: `http://localhost:8000/auth`
4. Copy the generated **Client ID** and **Client Secret** into your `.env` file.

### How to set SESSION_SECRET_KEY
- Generate a random string (at least 32 characters). Example (Python):
  ```python
  import secrets; print(secrets.token_urlsafe(32))
  ```
- Paste the value into your `.env` file as `SESSION_SECRET_KEY`. 


## 📋 Available MCP Tools

The MCP server exposes several tools for email automation:

### Authentication Tools
- **`get_authentication_status`** - Check if you're authenticated and see token status
- **`authenticate_user`** - Get a login link to authenticate with Google OAuth
- **`check_user_tokens`** - Debug tool to check if user tokens file exists and can be loaded
- **`list_authenticated_accounts`** - List all authenticated email accounts with their status

### Email Automation Tools
- **`run_email_automation_workflow`** - Complete email automation workflow (read, categorize, draft, schedule)
  - Parameters: `max_emails`, `tone`, `schedule_time`, `email_address` (optional)
- **`send_scheduled_emails`** - Send all due emails immediately
  - Parameters: `email_address` (optional)
- **`list_scheduled_emails`** - List all currently scheduled emails
- **`view_inbox_emails`** - View emails from your Gmail inbox
  - Parameters: `max_emails`, `email_address` (optional)

### Multi-Account Support

All email tools now support multiple authenticated accounts:

- **Specify an account**: Add `email_address` parameter to any tool to use a specific account
- **Default behavior**: If no email is specified, uses the first authenticated account
- **Account management**: Use `list_authenticated_accounts` to see all available accounts

**Examples:**
- `view_inbox_emails(email_address="user1@gmail.com")` - View inbox for specific account
- `run_email_automation_workflow(email_address="user2@gmail.com")` - Run automation for specific account
- `send_scheduled_emails(email_address="user1@gmail.com")` - Send scheduled emails for specific account

## 🔄 Workflow Steps

1. **Read Emails**: Connect to Gmail and fetch latest emails
2. **Categorize**: AI-powered email classification (urgent, spam, normal, etc.)
3. **Draft Responses**: Generate personalized replies using sender names
4. **Schedule**: Queue emails for later sending

## 🛡️ Security

- Environment-based configuration
- App password authentication
- Local LLM processing (no data sent to external APIs)
- Secure credential management

## 📚 Example Workflows

See `example_workflows.md` for sample email automation flows.

## 🔗 Integration

This MCP server can be integrated with any MCP-compatible AI assistant, providing powerful email automation capabilities through a single tool call.

## 🤖 Linking MCP Tool to Claude

To connect the Email MCP Assistant to Claude, add the following to your Claude config (replace `path` with your actual project path):

```json
"Email Assistant MCP": {
  "command": "path\\uv.EXE",
  "args": [
    "run",
    "--with-requirements",
    "path\\requirements.txt",
    "--with",
    "fastmcp",
    "fastmcp",
    "run",
    "path\\mcp_server.py"
  ]
}
```

- Make sure to use double backslashes (`\\`) in the path for Windows compatibility.
- This will launch the MCP server in a way compatible with Claude's tool integration.

## ⚙️ Environment Setup

Before running the project, you must create a `.env` file in the project root with the following variables:

```env
# Gmail IMAP/SMTP servers
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_SMTP_SERVER=smtp.gmail.com

# Google OAuth2 credentials (required for Gmail API access)
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret

# Session secret key (for FastAPI session security)
SESSION_SECRET_KEY=your-random-session-secret-key

# (Optional, for legacy direct login/testing only)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password-or-access-token
```

### How to get Google OAuth2 credentials
1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Create a new OAuth 2.0 Client ID (type: Web application).
3. Set the redirect URI to: `http://localhost:8000/auth`
4. Copy the generated **Client ID** and **Client Secret** into your `.env` file.

### How to set SESSION_SECRET_KEY
- Generate a random string (at least 32 characters). Example (Python):
  ```python
  import secrets; print(secrets.token_urlsafe(32))
  ```
- Paste the value into your `.env` file as `SESSION_SECRET_KEY`. 

- The MCP server is now based on FastMCP (a drop-in replacement for FastAPI for MCP tools).
