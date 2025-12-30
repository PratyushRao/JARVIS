import os
import io
import uuid
import json
import wave
import subprocess

import torch
import numpy as np
import soundfile as sf

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from vosk import Model, KaldiRecognizer
from transformers import (
    SpeechT5Processor,
    SpeechT5ForTextToSpeech,
    SpeechT5HifiGan
)

# =====================
# CONFIG
# =====================

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
BASE_DIR = r"C:\Users\praty\OneDrive\Desktop\Jarvis\JARVIS\backend"

# =====================
# FASTAPI APP
# =====================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# SPEECH TO TEXT (VOSK)
# =====================

VOSK_MODEL_PATH = os.path.join(BASE_DIR,"SpeechToText", "vosk-model-small-en-us-0.15")

if not os.path.exists(VOSK_MODEL_PATH):
    raise RuntimeError("Vosk model not found")

vosk_model = Model(VOSK_MODEL_PATH)

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    webm_path = f"{uid}.webm"
    wav_path = f"{uid}.wav"

    # Save uploaded file
    with open(webm_path, "wb") as f:
        f.write(await file.read())

    # Convert webm → wav (16kHz mono)
    subprocess.run(
        [
            FFMPEG_PATH,
            "-y",
            "-i",
            webm_path,
            "-ar", "16000",
            "-ac", "1",
            wav_path
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    wf = wave.open(wav_path, "rb")
    rec = KaldiRecognizer(vosk_model, wf.getframerate())
    rec.SetWords(True)

    result_text = ""

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            result_text += result.get("text", "") + " "

    final_result = json.loads(rec.FinalResult())
    result_text += final_result.get("text", "")

    wf.close()
    os.remove(webm_path)
    os.remove(wav_path)

    return {"text": result_text.strip()}

# =====================
# TEXT TO SPEECH (SpeechT5)
# =====================

# Load speaker embedding
embedding_path = r"C:\Users\praty\OneDrive\Desktop\Jarvis\JARVIS\backend\TextToSpeech\speaker_embedding.txt"
embedding = np.loadtxt(embedding_path)
speaker_embedding = torch.tensor(embedding, dtype=torch.float32).unsqueeze(0)

# Load models ONCE
processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
tts_model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

@app.post("/tts")
def text_to_speech(text: str):
    inputs = processor(text=text, return_tensors="pt")

    speech = tts_model.generate_speech(
        inputs["input_ids"],
        speaker_embeddings=speaker_embedding
    )

    audio = vocoder(speech).detach().cpu().numpy().squeeze()
    audio = np.clip(audio, -1.0, 1.0)

    buffer = io.BytesIO()
    sf.write(buffer, audio, samplerate=16000, format="WAV")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="audio/wav")
