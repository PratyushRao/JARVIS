/* src/App.tsx */
import { useRef, useState, useEffect } from "react";
import "./App.css";

interface Message {
  sender: "user" | "jarvis";
  text: string;
}

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Auto scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // =====================
  // VOICE RECORDING
  // =====================

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    mediaRecorderRef.current = recorder;
    audioChunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunksRef.current.push(e.data);
    };

    recorder.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
      await handleAudioSubmit(audioBlob);
      stream.getTracks().forEach((t) => t.stop());
    };

    recorder.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  // =====================
  // AUDIO SUBMIT
  // =====================

  const handleAudioSubmit = async (audioBlob: Blob) => {
    setIsProcessing(true);

    const formData = new FormData();
    formData.append("file", audioBlob, "speech.webm");

    const res = await fetch("http://127.0.0.1:8000/stt", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (data.text) {
      addMessage("user", data.text);
      await processResponse(data.text);
    }

    setIsProcessing(false);
  };

  // =====================
  // TEXT SUBMIT
  // =====================

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;

    addMessage("user", textInput);
    setIsProcessing(true);
    await processResponse(textInput);
    setTextInput("");
    setIsProcessing(false);
  };

  // =====================
  // LLM LOGIC
  // =====================

  const processResponse = async (text: string) => {
    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    const data = await res.json();
    addMessage("jarvis", data.response);
    await speakText(data.response);
  };

  // =====================
  // TTS
  // =====================

  const speakText = async (text: string) => {
    const res = await fetch(
      `http://127.0.0.1:8000/tts?text=${encodeURIComponent(text)}`,
      { method: "POST" }
    );

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);

    if (audioPlayerRef.current) {
      audioPlayerRef.current.src = url;
      audioPlayerRef.current.play();
      setIsSpeaking(true);
      audioPlayerRef.current.onended = () => setIsSpeaking(false);
    }
  };

  const addMessage = (sender: "user" | "jarvis", text: string) => {
    setMessages((prev) => [...prev, { sender, text }]);
  };

  return (
    <div className="jarvis-container">
      {/* HEADER */}
      <h1 style={{ letterSpacing: "5px", textShadow: "0 0 10px red" }}>
        J.A.R.V.I.S
      </h1>

      {/* ORB */}
      <div className="orb-container">
        <div
          className={`arc-reactor 
            ${isRecording ? "listening" : ""} 
            ${isProcessing ? "processing" : ""} 
            ${isSpeaking ? "speaking" : ""}`}
        />
      </div>

      {/* CHAT */}
      <div className="chat-window">
        {messages.length === 0 && (
          <div className="system-text">System Online. Awaiting Input...</div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}

        <div ref={chatEndRef} />
      </div>

      {/* INPUT */}
      <form className="input-area" onSubmit={handleTextSubmit}>
        <input
          type="text"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Type a command..."
          disabled={isProcessing || isRecording}
        />

        <button type="submit" disabled={!textInput || isProcessing}>
          SEND
        </button>

        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          className={isRecording ? "mic-active" : ""}
          disabled={isProcessing}
        >
          {isRecording ? "STOP" : "VOICE"}
        </button>


        {/* Add the button functions here later */}
        <button type="button" disabled={isProcessing}> 
          SHOW
        </button>
      </form>

      <audio ref={audioPlayerRef} hidden />
    </div>
  );
}

export default App;
