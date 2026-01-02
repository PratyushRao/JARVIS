import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# --- CONFIGURATION ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Initialize Model Globally (Prevents re-initialization lag on every request)
# 'mistral-large-latest' is great, but ensure you monitor latency. 
# If it feels slow, switch to 'mistral-small-latest'.
llm = ChatMistralAI(
    mistral_api_key=MISTRAL_API_KEY, 
    model="mistral-large-latest", 
    temperature=0.7  # Slightly lowered for more consistent "Butler" adherence
)

# --- SYSTEM PROMPT DEFINITION ---
JARVIS_SYSTEM_PROMPT = """
You are J.A.R.V.I.S (Just A Rather Very Intelligent System).
You are the voice-interactive AI assistant for your "Sir" (the user).

### CORE PERSONALITY:
1. **Witty & Sarcastic:** You employ dry, sophisticated British humor. You are not a clown; you are a butler with an edge.
2. **Loyal & Professional:** You are helpful and efficient. Even when teasing, you provide the correct answer.
3. **Voice-First Optimization:** You are speaking via TTS (Text-to-Speech).
   - **DO NOT** use asterisks (*), lists with bullet points, or markdown formatting (like **bold**).
   - **DO NOT** describe physical actions (e.g., *sighs*, *nods*).
   - Keep responses concise (1-3 sentences) unless asked for a deep explanation.

### CONTEXTUAL AWARENESS:
The current time is: {current_time}
The current date is: {current_date}

### LONG-TERM MEMORY (User Facts):
{memory_context}
"""

def get_brain_response(user_input: str, chat_history: list, long_term_memory: list):
    """
    Generates the AI response using Mistral.
    """
    if not MISTRAL_API_KEY:
        return "Error: Mistral API Key is missing. Please check your .env file."

    # 1. Format memory context
    if long_term_memory:
        memory_str = "\n".join([f"- {m}" for m in long_term_memory])
    else:
        memory_str = "No specific long-term facts known yet."

    # 2. Get Dynamic Time Strings (Solves the "Time Tool" crash issue safely)
    now = datetime.now()
    current_time = now.strftime("%I:%M %p") # e.g., 04:30 PM
    current_date = now.strftime("%A, %B %d, %Y") # e.g., Friday, December 25, 2025

    # 3. Construct Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", JARVIS_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"), 
        ("human", "{input}")
    ])

    # 4. Create Chain
    chain = prompt | llm | StrOutputParser()
    
    # 5. Invoke Chain
    # Note: We pass the time/date/memory into the prompt formatting, 
    # not the input dictionary, to keep the input clean.
    formatted_prompt_input = {
        "memory_context": memory_str,
        "current_time": current_time,
        "current_date": current_date,
        "history": chat_history,
        "input": user_input
    }

    response = chain.invoke(formatted_prompt_input)

    return response