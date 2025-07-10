from tools.read_mail import read_inbox_emails
from tools.categorize_mail import categorize_emails
from tools.draft_mail import draft_email_response
from tools.schedule_mail import schedule_email_send
import asyncio
from typing import Any, Dict
# Import the correct graph builder from langgraph
from langgraph.graph import StateGraph, START, END
import datetime

# Define State as a plain dict for LangGraph compatibility
State = dict

# --- Node wrappers for state dicts ---
async def node_read_mail(state: Dict) -> Dict:
    state_out = dict(state)  # Copy all keys
    emails = await read_inbox_emails(
        state["imap_server"],
        state["email"],
        state["access_token"],
        state.get("max_emails", 10)
    )
    state_out["emails"] = emails
    return state_out

async def node_categorize_mail(state: Dict) -> Dict:
    state_out = dict(state)  # Copy all keys
    emails = state["emails"]
    categorized = await categorize_emails(emails)
    state_out["emails"] = categorized
    return state_out

async def node_draft_mail(state: Dict) -> Dict:
    state_out = dict(state)  # Copy all keys
    emails = state["emails"]
    tone = state.get("tone", "polite")
    drafted = []
    for mail in emails:
        draft = await draft_email_response(mail, tone)
        mail["draft"] = draft
        drafted.append(mail)
    state_out["emails"] = drafted
    return state_out

async def node_schedule_mail(state: Dict) -> Dict:
    state_out = dict(state)  # Copy all keys
    emails = state["emails"]
    send_time = state["send_time"]
    user_email = state["email"]  # Get the user's email address
    for mail in emails:
        mail["to"] = mail.get("from")  # Send to the original sender
        mail["from"] = user_email  # Send from the user's email
        scheduled = schedule_email_send(mail, send_time)
        mail["scheduled"] = scheduled
    state_out["emails"] = emails
    return state_out

# --- Build the workflow graph using StateGraph ---
workflow = StateGraph(State)
workflow.add_node("read_mail", node_read_mail)
workflow.add_node("categorize_mail", node_categorize_mail)
workflow.add_node("draft_mail", node_draft_mail)
workflow.add_node("schedule_mail", node_schedule_mail)

# Define the workflow: read -> categorize -> draft -> schedule
workflow.add_edge(START, "read_mail")
workflow.add_edge("read_mail", "categorize_mail")
workflow.add_edge("categorize_mail", "draft_mail")
workflow.add_edge("draft_mail", "schedule_mail")
workflow.add_edge("schedule_mail", END)

compiled_workflow = workflow.compile()

async def run_workflow(imap_server: str, smtp_server: str, email: str, access_token: str, send_time: str = None, tone: str = "polite", max_emails: int = 10) -> Any:
    """
    Executes the email automation workflow using the compiled LangGraph graph.
    Returns the final state from the workflow.
    """
    if not send_time:
        send_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=0)).replace(microsecond=0).isoformat()
    state = {
        "imap_server": imap_server,
        "smtp_server": smtp_server,
        "email": email,
        "access_token": access_token,
        "send_time": send_time,
        "tone": tone,
        "max_emails": max_emails
    }
    result = await compiled_workflow.ainvoke(state)
    return result["emails"]

# Example usage (for testing):
# asyncio.run(run_workflow(imap_server, smtp_server, email, access_token, send_time="2024-06-01T10:00:00Z"))

# TODO: Integrate this function with the MCP server for real workflow execution 