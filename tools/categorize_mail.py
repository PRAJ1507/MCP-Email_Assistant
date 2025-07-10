from typing import List, Dict
from langchain_ollama.llms import OllamaLLM
import asyncio

# Initialize Ollama LLM (assumes Ollama is running locally)
llm = OllamaLLM(model="llama3.2")  # You can change the model name if needed

async def categorize_emails(emails: List[Dict]) -> List[Dict]:
    """
    Categorizes emails by priority or topic using Ollama LLM.
    Adds a 'category' field: e.g., 'urgent', 'newsletter', 'normal', 'spam', 'social', 'promotion'.
    """
    for mail in emails:
        subject = mail.get('subject', '')
        snippet = mail.get('snippet', '')
        prompt = (
            f"Classify the following email into one of these categories: urgent, newsletter, normal, spam, social, promotion.\n"
            f"Subject: {subject}\n"
            f"Body: {snippet}\n"
            f"Return only the category name."
        )
        try:
            loop = asyncio.get_event_loop()
            category = await loop.run_in_executor(None, lambda: llm.invoke(prompt))
            mail['category'] = category.strip().lower()
        except Exception as e:
            mail['category'] = f"[LLM Error: {e}]"
    return emails 