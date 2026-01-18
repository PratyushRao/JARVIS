import sys
import pathlib
# Allow running this file directly from the `backend/` directory for convenience.
# Prefer `python -m backend.main` from repo root, but if someone runs `python main.py`
# ensure the project root is on sys.path so `import backend.*` works.
if __package__ is None:
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

import os
import io
import uuid
import subprocess
import edge_tts 
import re
from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List

# Import your modules
from backend.brain import memory_manager as mem
from backend.brain import llm_services as brain
from langchain_core.messages import HumanMessage, AIMessage
from faster_whisper import WhisperModel

# =====================
# CONFIG
# =====================
import shutil
FFMPEG_PATH = shutil.which("ffmpeg") or r"C:\ffmpeg\bin\ffmpeg.exe"  # Try to find ffmpeg in PATH first
app = FastAPI()

# Allow your Frontend (npm run dev) to talk to this Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper once on startup
print("⏳ Loading Whisper Model...")
whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")
print("✅ Whisper Model Loaded!")

# Preload multimodal model for faster image processing
print("⏳ Preloading Multimodal Model...")
try:
    from backend.brain import local_multimodal
    if local_multimodal.is_available():
        # Force model loading now
        local_multimodal._init_model()
        print("✅ Multimodal Model Preloaded!")
    else:
        print("⚠️ Multimodal Model not available")
except Exception as e:
    print(f"⚠️ Failed to preload multimodal model: {e}")

# =====================
# REQUEST MODELS
# =====================
class ChatRequest(BaseModel):
    text: str
    # 'alias' allows the frontend to send "chatId" (JS style) 
    # while Python uses "chat_id"
    chat_id: Optional[str] = Field(None, alias="chatId") 

class ChatResponse(BaseModel):
    response: str
    chat_id: str

class RenameRequest(BaseModel):
    new_name: str

class TTSRequest(BaseModel):
    text: str

# =====================
# 1. MANAGEMENT ENDPOINTS (For Sidebar)
# =====================

@app.get("/chats")
def list_chats():
    """Returns a list of all chats for the sidebar: [{id, name}, ...]"""
    return mem.get_all_chats()

@app.post("/chats/new")
def create_chat():
    """Creates a new chat and returns its ID and Name"""
    return mem.create_new_chat()

@app.put("/chats/{chat_id}")
def rename_chat(chat_id: str, req: RenameRequest):
    """Renames a specific chat"""
    success = mem.rename_chat(chat_id, req.new_name)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "new_name": req.new_name}

@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: str):
    """Deletes a chat"""
    success = mem.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success"}

@app.get("/chats/{chat_id}/history")
def get_history(chat_id: str):
    """Returns the message history for a specific chat"""
    return mem.get_chat_history(chat_id)

# =====================
# 2. CHAT & BRAIN ENDPOINT
# =====================

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    user_text = req.text
    chat_id = req.chat_id

    # If frontend didn't send an ID, create a new one
    if not chat_id:
        new_chat = mem.create_new_chat()
        chat_id = new_chat["chat_id"]

    # 1. Get History
    history_dicts = mem.get_chat_history(chat_id)
    
    # 2. Convert to LangChain format
    langchain_history = []
    for h in history_dicts:
        if h["role"] == "human":
            langchain_history.append(HumanMessage(content=h["content"]))
        else:
            langchain_history.append(AIMessage(content=h["content"]))

    # 3. Get LTM
    long_term_mem = mem.get_long_term_memory()

    # 4. Generate Response
    # This calls your NEW llm_services.py function
    ai_response = brain.get_brain_response(user_text, langchain_history, long_term_mem)

    # 5. Save to DB
    mem.append_to_chat(chat_id, "human", user_text)
    mem.append_to_chat(chat_id, "ai", ai_response)

    # 6. Auto-Save "My Name is" (Basic LTM Trigger)
    if "my name is" in user_text.lower():
        mem.add_long_term_memory(f"User Mentioned: {user_text}")

    return ChatResponse(response=ai_response, chat_id=chat_id)

# =====================
# 3. IMAGE QUESTION ENDPOINT
# =====================
@app.post("/image_qa", response_model=ChatResponse)
async def image_question(file: UploadFile = File(...), question: str = Form(...), chat_id: Optional[str] = Form(None)):
    """Accepts an image file and a question, returns an image-aware response."""
    # 1. Ensure chat id exists
    if not chat_id:
        new_chat = mem.create_new_chat()
        chat_id = new_chat["chat_id"]

    # 2. Read file bytes
    contents = await file.read()

    # 3. Use optimized multimodal LLM for all questions
    try:
        from backend.brain import local_multimodal
        if local_multimodal and local_multimodal.is_available():
            ans, err = local_multimodal.analyze_image_with_local_llm(contents, question)
            if ans and not err:
                mem.append_to_chat(chat_id, "human", f"[Image: {file.filename}] {question}")
                mem.append_to_chat(chat_id, "ai", ans)
                return ChatResponse(response=ans, chat_id=chat_id)
    except Exception as e:
        print(f"Multimodal analysis error: {e}")

    # 4. If multimodal fails, give helpful error
    ai_response = "I'm unable to analyze this image right now. The multimodal model may still be loading or encountered an error."

    mem.append_to_chat(chat_id, "human", f"[Image: {file.filename}] {question}")
    mem.append_to_chat(chat_id, "ai", ai_response)

    return ChatResponse(response=ai_response, chat_id=chat_id)


@app.get("/status")
def service_status():
    """Lightweight endpoint to check model/service availability.

    Returns JSON describing whether GROQ key is present, whether the Brain successfully
    initialized, whether the local multimodal model or caption libs appear available.
    """
    try:
        from backend.brain import llm_services
        return llm_services.check_status()
    except Exception as e:
        return {"error": str(e)}


# =====================
# 4. VOICE ENDPOINTS (STT & TTS)
# =====================

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    webm_path = f"{uid}.webm"
    wav_path = f"{uid}.wav"

    with open(webm_path, "wb") as f:
        f.write(await file.read())

    try:
        # Convert WebM to WAV (16kHz, Mono) for Whisper
        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", webm_path, "-ar", "16000", "-ac", "1", wav_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
    except Exception as e:
        print(f"FFmpeg Error: {e}")
        return {"error": "FFmpeg conversion failed"}

    segments, _ = whisper_model.transcribe(wav_path, language="en", vad_filter=True)
    text = " ".join(s.text for s in segments)

    # Cleanup temp files
    if os.path.exists(webm_path): os.remove(webm_path)
    if os.path.exists(wav_path): os.remove(wav_path)

    return {"text": text.strip()}

@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    """
    Accepts JSON: {"text": "Hello world"}
    Returns: Audio stream (MP3)
    """
    text = req.text
    if not text.strip():
        return {"error": "No text provided"}

    # Cleanup text for better audio (remove markdown, special chars)
    clean_text = re.sub(r'[*#`_~]', '', text) 
    
    output_file = f"tts_{uuid.uuid4().hex}.mp3"
    
    # Generate Audio
    communicate = edge_tts.Communicate(clean_text, "en-GB-RyanNeural")
    await communicate.save(output_file)
    
    # Read file to memory
    with open(output_file, "rb") as f:
        audio_data = f.read()
    
    # Cleanup file
    os.remove(output_file)
    
    return StreamingResponse(io.BytesIO(audio_data), media_type="audio/mpeg")

# =====================
# RUNNER
# =====================
if __name__ == "__main__":
    import uvicorn
    print("🚀 JARVIS Backend running on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
