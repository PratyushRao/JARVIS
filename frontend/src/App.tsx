import { useState, useRef } from "react";
import axios from "axios";
import { Mic, Square, Loader2 } from "lucide-react";

type Message = {
  role: "user" | "ai";
  text: string;
};

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const options = { mimeType: "audio/webm" };
      const recorder = MediaRecorder.isTypeSupported(options.mimeType) 
        ? new MediaRecorder(stream, options) 
        : new MediaRecorder(stream);

      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: recorder.mimeType });
        await sendAudioToBackend(audioBlob);
      };

      recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error(error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const sendAudioToBackend = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    try {
      const { data } = await axios.post("http://127.0.0.1:8000/process-voice", formData);
      
      setMessages(prev => [
        ...prev,
        { role: "user", text: data.user_text },
        { role: "ai", text: data.jarvis_text }
      ]);

      if (data.audio_url) playResponse(data.audio_url);
    } catch (error) {
      setMessages(prev => [...prev, { role: "ai", text: "Transcription failed." }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const playResponse = (url: string) => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.src = url;
      audioPlayerRef.current.play();
      setIsSpeaking(true);
      audioPlayerRef.current.onended = () => setIsSpeaking(false);
    }
  };

  return (
    <div className="app-container">
      <h1>J.A.R.V.I.S</h1>
      <div className="orb-container">
        <div className={`orb ${isRecording ? "listening" : ""} ${isProcessing ? "thinking" : ""} ${isSpeaking ? "speaking" : ""}`} />
      </div>
      <p>{isRecording ? "Listening..." : isProcessing ? "Thinking..." : isSpeaking ? "Speaking..." : "Online"}</p>
      <button 
        onClick={isRecording ? stopRecording : startRecording} 
        disabled={isProcessing || isSpeaking}
      >
        {isProcessing ? <Loader2 className="animate-spin" /> : isRecording ? <Square /> : <Mic />}
      </button>
      <div className="chat-log">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <strong>{msg.role.toUpperCase()}:</strong> {msg.text}
          </div>
        ))}
      </div>
      <audio ref={audioPlayerRef} hidden />
    </div>
  );
}

export default App;