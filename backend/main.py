import os
import sys
import warnings
import logging
import asyncio
import pathlib
import json
import io
import uuid
import subprocess
import re
import shutil
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, status, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from faster_whisper import WhisperModel
import edge_tts

# ---------------- ENV SILENCING ----------------
os.environ["HF_HUB_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
# -----------------------------------------------

# Repo path fix
if __package__ is None:
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

# Internal imports (lazy usage)
import auth
from brain import memory_manager as mem
from brain import llm_services as brain
from brain import web_search as searcher
from langchain_core.messages import HumanMessage, AIMessage

# ---------------- CONFIG ----------------
FFMPEG_PATH = shutil.which("ffmpeg")
connected_agent = None
agent_lock = asyncio.Lock()

whisper_model = None
whisper_lock = asyncio.Lock()

# ---------------- LIFESPAN ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 JARVIS backend ready (Render-safe)")
    yield

# ---------------- APP ----------------
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jarvis-byte-me.vercel.app",
        "https://jarvis-byte-me.vercel.app/",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- MODELS ----------------
class ChatRequest(BaseModel):
    text: str
    chat_id: Optional[str] = Field(None, alias="chatId")

class ChatResponse(BaseModel):
    response: str
    chat_id: str

class RenameRequest(BaseModel):
    new_name: str

class TTSRequest(BaseModel):
    text: str

class SignupRequest(BaseModel):
    username: str
    password: str

# ---------------- HELPERS ----------------
def extract_first_json(text: str):
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        if depth == 0:
            return text[start:i+1]
    return None

def perform_search(query: str):
    tool = searcher.get_search_tool()
    try:
        result = tool.func(query)
        return str(result)[:2000]
    except Exception as e:
        print("Search error:", e)
        return "Search failed."

async def get_whisper():
    global whisper_model
    async with whisper_lock:
        if whisper_model is None:
            whisper_model = WhisperModel(
                "tiny.en",
                device="cpu",
                compute_type="int8"
            )
    return whisper_model

# ---------------- ROOT ----------------
@app.get("/")
def root():
    return {"status": "Backend is running!"}

# ---------------- AUTH ----------------
@app.post("/signup")
def signup(user: SignupRequest):
    if auth.get_user(user.username):
        raise HTTPException(400, "Username already exists")
    auth.create_user_in_db(user.username, user.password)
    return {"status": "ok"}

@app.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = auth.get_user(form.username)
    if not user or not auth.verify_password(form.password, user["hashed_password"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    token = auth.create_access_token({"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users/me")
def me(current_user: dict = Depends(auth.get_current_user)):
    return {"username": current_user["username"]}

# ---------------- CHAT ----------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user=Depends(auth.get_current_user)):
    user_id = current_user["username"]
    chat_id = req.chat_id or mem.create_new_chat(user_id)["chat_id"]

    history = mem.get_chat_history(chat_id, user_id)
    lc_history = [
        HumanMessage(h["content"]) if h["role"] == "human" else AIMessage(h["content"])
        for h in history
    ]

    long_mem = mem.get_long_term_memory(user_id)
    ai_response = brain.get_brain_response(req.text, lc_history, long_mem)
    ai_response = ai_response.replace("```json", "").replace("```", "")

    mem.append_to_chat(chat_id, "human", req.text, user_id)
    mem.append_to_chat(chat_id, "ai", ai_response, user_id)

    return ChatResponse(response=ai_response, chat_id=chat_id)

# ---------------- STT ----------------
@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    if not FFMPEG_PATH:
        raise HTTPException(503, "STT unavailable")

    uid = uuid.uuid4().hex
    webm = f"{uid}.webm"
    wav = f"{uid}.wav"

    try:
        with open(webm, "wb") as f:
            f.write(await file.read())

        subprocess.run(
            [FFMPEG_PATH, "-y", "-i", webm, "-ar", "16000", "-ac", "1", wav],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        model = await get_whisper()
        result = model.transcribe(wav, language="en")
        text = " ".join(seg["text"] for seg in result["segments"])

        return {"text": text.strip()}
    finally:
        for p in [webm, wav]:
            if os.path.exists(p):
                os.remove(p)

# ---------------- TTS ----------------
@app.post("/tts")
async def tts(req: TTSRequest):
    clean = re.sub(r'[*#`_~]', '', req.text)
    out = f"tts_{uuid.uuid4().hex}.mp3"
    try:
        await edge_tts.Communicate(clean, "en-GB-RyanNeural").save(out)
        return StreamingResponse(open(out, "rb"), media_type="audio/mpeg")
    finally:
        if os.path.exists(out):
            os.remove(out)

# ---------------- RUN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
    )
