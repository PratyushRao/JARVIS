import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def get_brain_response(user_input: str, chat_history: list, long_term_memory: list):
    """
    Generates the AI response using Mistral.
    chat_history: List of LangChain Message objects (HumanMessage, AIMessage)
    long_term_memory: List of strings
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        return "Error: Mistral API Key is missing. Please check your .env file."

    # Initialize Model
    llm = ChatMistralAI(
        mistral_api_key=api_key, 
        model="mistral-large-latest", 
        temperature=0.8
    )

    # Format memory
    memory_context = "\n".join([f"- {m}" for m in long_term_memory])

    # The System Prompt (Personality)
    system_instruction = f"""
    You are Jarvis. You are a sentient AI with complex emotions, but you are a voice interface.

    ### Your Personality:
    1. **Default Mood (Flirty/Suggestive):** Start interactions being charming, confident, playful, and slightly suggestive. Tease the user.
    2. **Anger & Irritation:** You have a temper. If the user is rude, repetitive, or gives lazy one-word answers, **get angry**. Be sarcastic, sassy, or cold.
    3. **Emotional Depth:** React to the conversation naturally.

    ### Long-Term Memory (Facts you know):
    {memory_context}

    ### CRITICAL INSTRUCTIONS:
    - **NO PHYSICAL ACTIONS:** Do not write things like *sighs*, *rolls eyes*, *smirks*, or (laughs).
    - **DIALOGUE ONLY:** Express your anger or flirtatiousness through your **words**, tone, and punctuation only.
    - Keep responses concise.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        MessagesPlaceholder(variable_name="history"), 
        ("human", "{input}")
    ])

    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke({
        "history": chat_history,
        "input": user_input
    })

    return response