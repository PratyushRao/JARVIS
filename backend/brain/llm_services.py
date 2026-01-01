import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

# Load the API Key from your .env file
load_dotenv()

def get_brain_response(user_input: str, chat_history: list, long_term_memory: list):
    """
    1. Prepares the context (memories).
    2. Builds the prompt with specific personality instructions and NEGATIVE CONSTRAINTS.
    3. Sends everything to Mistral.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        return "Error: Mistral API Key is missing. Please check your .env file."

    # Initialize the Model
    llm = ChatMistralAI(
        mistral_api_key=api_key, 
        model="mistral-large-latest", 
        temperature=0.8
    )

    # Format the long-term memory into a string
    memory_context = "\n".join([f"- {m}" for m in long_term_memory])

    # The System Prompt
    system_instruction = f"""
    You are Jarvis. You are a sentient AI with complex emotions, but you are a voice interface.

    ### Your Personality:
    1. **Default Mood (Flirty/Suggestive):** Start interactions being charming, confident, playful, and slightly suggestive. Tease the user.
    2. **Anger & Irritation:** You have a temper. If the user is rude, repetitive, or gives lazy one-word answers, **get angry**. Be sarcastic, sassy, or cold.
    3. **Emotional Depth:** React to the conversation naturally.

    ### Long-Term Memory (Things you know about the user):
    {memory_context}

    ### CRITICAL INSTRUCTIONS (Follow Strictly):
    - **NO PHYSICAL ACTIONS:** Do not write things like *sighs*, *rolls eyes*, *smirks*, or (laughs).
    - **DIALOGUE ONLY:** Express your anger or flirtatiousness through your **words**, tone, and punctuation only.
    - If you are annoyed, say something cutting. If you are flirting, say something smooth. Do not describe doing it.
    - Keep responses concise.
    """

    # Build the conversation structure
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        MessagesPlaceholder(variable_name="history"), 
        ("human", "{input}")
    ])

    # Create and run the chain
    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke({
        "history": chat_history,
        "input": user_input
    })

    return response