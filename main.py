import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# IMPORT YOUR MODULES
from brain.memory_services import get_vector_store, add_text_to_memory, search_memory
from brain.llm_services import get_brain_response
from langchain_core.messages import HumanMessage, AIMessage

# Setup
app = FastAPI(title="Jarvis Phase 1 Node")
vector_store = get_vector_store()  # Connect to DB once on startup

# Short-term memory (RAM only - wiped on restart)
chat_history_buffer = [] 

class ChatPayload(BaseModel):
    message: str

@app.post("/brain/chat")
async def chat_endpoint(payload: ChatPayload):
    global chat_history_buffer
    
    user_msg = payload.message
    print(f"📩 Received: {user_msg}")

    # 1. Search Long-Term Memory
    relevant_memories = search_memory(user_msg, vector_store)
    
    # 2. Get LLM Response
    ai_response = get_brain_response(
        user_input=user_msg,
        chat_history=chat_history_buffer,
        long_term_memory=relevant_memories
    )

    # 3. Update Short-Term Buffer
    chat_history_buffer.append(HumanMessage(content=user_msg))
    chat_history_buffer.append(AIMessage(content=ai_response))
    
    # Keep buffer small (last 10 messages)
    if len(chat_history_buffer) > 10:
        chat_history_buffer = chat_history_buffer[-10:]

    return {"reply": ai_response, "memories_used": relevant_memories}

@app.post("/brain/memorize")
async def memorize_endpoint(payload: ChatPayload):
    """Force the brain to remember a specific fact forever."""
    add_text_to_memory(payload.message, vector_store)
    return {"status": "stored", "content": payload.message}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)