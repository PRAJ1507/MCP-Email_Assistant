# Security Policy for Email MCP Assistant

## Authentication

- All API endpoints are protected using OAuth2 authentication (Google as provider).
- Only authenticated users can access workflow execution endpoints.
- OAuth2 tokens and user sessions are stored securely using server-side session storage (FastAPI SessionMiddleware).
- Tokens are never logged or exposed.

## Data Protection

- User sessions and tokens are stored securely using server-side session storage.
- Sensitive data (such as email content) is only accessible to the authenticated user.
- All communication with the server must use HTTPS in production.

## User Data

- Each user's data (emails, scheduled actions) is isolated and not accessible by other users.
- User-specific data is stored securely and deleted upon user request.

## Best Practices

- Regularly update dependencies to patch security vulnerabilities.
- Use environment variables for all secrets and credentials (e.g., Google OAuth client ID/secret, session secret).
- Monitor and log authentication attempts for suspicious activity (without logging sensitive tokens).

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it by opening an issue or contacting the maintainer directly. 

---

## Technical Details

### Token Refresh and Protection

- **OAuth2 Token Storage:**
  - After Google OAuth2 login, access and refresh tokens, plus expiration, are stored in `user_tokens.json` (never committed to version control).
  - Tokens are never logged or exposed in logs.
- **Token Refresh Logic:**
  - On token expiry, the system checks for a refresh token and, if present, requests a new access token from Google.
  - The new token and expiration are updated in `user_tokens.json`.
  - If no refresh token is available, the user must re-authenticate.
- **Session Security:**
  - FastAPI’s `SessionMiddleware` stores session data securely server-side, with a secret key set via environment variable.

### Scheduled Email Protection

- **User Isolation:**
  - Scheduled emails are stored in `scheduled_emails.json` and tagged with the sender’s email address.
  - The scheduler only processes and sends emails for the authenticated user (matching the `from` field).
- **Token Validation:**
  - Before sending, the system checks if the user’s access token is valid and refreshes it if needed.
  - If refreshing fails, the email is not sent and the user is prompted to re-authenticate.

### Scheduler and User Data Interaction

- **Background Scheduler:**
  - Runs in the background (APScheduler) and checks for due emails for all authenticated users.
  - Loads and refreshes each user’s token as needed.
  - Only processes emails scheduled by the user whose token is being used.
- **Multi-Account Support:**
  - Supports multiple authenticated accounts, each with isolated tokens and scheduled emails.
  - All user data is kept isolated; actions are always performed in the context of the authenticated user.

### Additional Security Practices

- **Environment Variables:**
  - All sensitive credentials (Google OAuth client ID/secret, session secret key) are stored in environment variables.
- **HTTPS Requirement:**
  - All communication should use HTTPS in production to protect tokens and user data in transit.
- **No Token Logging:**
  - Tokens are never printed in logs or error messages.
- **User Data Deletion:**
  - User data can be deleted upon request for privacy and compliance. 