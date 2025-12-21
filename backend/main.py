import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
from brain.speech_services import transcribe_audio, generate_speech

app = FastAPI()

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directory for generated audio files
os.makedirs("generated_audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="generated_audio"), name="audio")

@app.get("/")
def read_root():
    return {"status": "Jarvis is Online"}

@app.post("/process-voice")
async def process_voice(file: UploadFile = File(...)):
    # Save incoming audio from browser
    temp_filename = "temp_input.webm" 
    
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Log file status
    file_size = os.path.getsize(temp_filename)
    print(f"Received file: {file.filename}, Size: {file_size} bytes")
    
    # Process speech to text
    print(f"Transcribing {temp_filename}...")
    user_text = transcribe_audio(temp_filename)
    print(f"User said: {user_text}")

    # Generate response text
    jarvis_response = f"You said: {user_text}. I am fully operational."
    
    # Process text to speech
    output_filename = "response.wav"
    file_path = os.path.join("generated_audio", output_filename)
    generate_speech(jarvis_response, file_path)

    return {
        "user_text": user_text,
        "jarvis_text": jarvis_response,
        "audio_url": f"http://127.0.0.1:8000/audio/{output_filename}" 
    }

# Start the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)