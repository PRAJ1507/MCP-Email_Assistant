from typing import Dict
from langchain_ollama.llms import OllamaLLM
import asyncio

# Initialize Ollama LLM (assumes Ollama is running locally)
llm = OllamaLLM(model="llama3.2")  # You can change the model name if needed

async def draft_email_response(email: Dict, tone: str = 'polite') -> str:
    """
    Drafts a personalized email response using Ollama LLM.
    The response is generated based on the email content and the specified tone.
    """
    subject = email.get('subject', '')
    snippet = email.get('snippet', '')
    sender = email.get('from', 'Sender')
    prompt = (
        f"Draft a {tone} reply to the following email.\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Body: {snippet}\n"
        f"Reply:"
    )
    try:
        loop = asyncio.get_event_loop()
        draft = await loop.run_in_executor(None, lambda: llm.invoke(prompt))
        return draft.strip()
    except Exception as e:
        return f"[LLM Error: {e}]" 