import { useRef, useState } from "react";

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioURL, setAudioURL] = useState<string | null>(null);
  const [aiVoiceURL, setAiVoiceURL] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);

    mediaRecorderRef.current = recorder;
    audioChunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunksRef.current.push(e.data);
    };

    recorder.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, {
        type: "audio/webm",
      });

      // Playback user's voice
      if (audioURL) URL.revokeObjectURL(audioURL);
      const url = URL.createObjectURL(audioBlob);
      setAudioURL(url);

      // Send to STT backend
      await sendAudioToBackend(audioBlob);

      recorder.stream.getTracks().forEach((track) => track.stop());
    };

    recorder.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const speakText = async (text: string) => {
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/tts?text=${encodeURIComponent(text)}`,
        { method: "POST" }
      );

      const audioBlob = await res.blob();

      if (aiVoiceURL) URL.revokeObjectURL(aiVoiceURL);
      const url = URL.createObjectURL(audioBlob);
      setAiVoiceURL(url);
    } catch (err) {
      console.error("TTS failed", err);
    }
  };

  const sendAudioToBackend = async (audioBlob: Blob) => {
    setIsProcessing(true);
    const formData = new FormData();
    formData.append("file", audioBlob, "speech.webm");

    try {
      const res = await fetch("http://127.0.0.1:8000/stt", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setTranscript(data.text);

      // Speak transcription
      await speakText(data.text);
    } catch (err) {
      console.error(err);
      setTranscript("Transcription failed");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ padding: "40px", textAlign: "center" }}>
      <h1>J.A.R.V.I.S</h1>

      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
      >
        {isRecording ? "Stop Recording" : "Start Recording"}
      </button>

      {isProcessing && <p>⏳ Processing...</p>}

      {audioURL && (
        <div style={{ marginTop: "20px" }}>
          <p>
            <strong>Your Voice:</strong>
          </p>
          <audio controls src={audioURL} />
        </div>
      )}

      {transcript && (
        <div style={{ marginTop: "20px" }}>
          <p>
            <strong>Transcription:</strong>
          </p>
          <p>{transcript}</p>
        </div>
      )}

      {aiVoiceURL && (
        <div style={{ marginTop: "20px" }}>
          <p>
            <strong>J.A.R.V.I.S Speaking</strong>
          </p>
          <audio controls autoPlay src={aiVoiceURL} />
        </div>
      )}
    </div>
  );
}

export default App;
