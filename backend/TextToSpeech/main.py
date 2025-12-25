import os
import torch
import numpy as np
import io
import soundfile as sf
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load speaker embedding
embedding = np.loadtxt(os.path.join(BASE_DIR, "speaker_embedding.txt"))
speaker_embedding = torch.tensor(embedding, dtype=torch.float32).unsqueeze(0)

# Load models ONCE
processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

@app.post("/tts")
def text_to_speech(text: str):
    inputs = processor(text=text, return_tensors="pt")

    speech = model.generate_speech(
        inputs["input_ids"],
        speaker_embeddings=speaker_embedding
    )

    audio = vocoder(speech).detach().cpu().numpy().squeeze()
    audio = np.clip(audio, -1.0, 1.0)

    buffer = io.BytesIO()
    sf.write(buffer, audio, samplerate=16000, format="WAV")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="audio/wav")
