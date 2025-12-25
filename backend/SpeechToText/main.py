from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from vosk import Model, KaldiRecognizer
import subprocess
import uuid
import wave
import json
import os

app = FastAPI()

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "vosk-model-small-en-us-0.15")

if not os.path.exists(MODEL_PATH):
    raise RuntimeError("Vosk model not found")

model = Model(MODEL_PATH)

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    # Save uploaded webm
    uid = uuid.uuid4().hex
    webm_path = f"{uid}.webm"
    wav_path = f"{uid}.wav"

    with open(webm_path, "wb") as f:
        f.write(await file.read())

    # Convert webm → wav (16kHz mono)
    subprocess.run(
        ["ffmpeg", "-y", "-i", webm_path, "-ar", "16000", "-ac", "1", wav_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Read wav for Vosk
    wf = wave.open(wav_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
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

    # Cleanup
    wf.close()
    os.remove(webm_path)
    os.remove(wav_path)

    return {"text": result_text.strip()}
