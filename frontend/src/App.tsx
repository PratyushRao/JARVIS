/* src/App.tsx */
import { useRef, useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import * as api from "./api"; 
import Sidebar from "./Sidebar"; // <--- Import the new component
import "./App.css";

interface Message {
  sender: "user" | "jarvis";
  text: string;
}

function App() {
  // --- CORE STATE ---
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  
  // --- UI STATE ---
  const [showSidebar, setShowSidebar] = useState(false);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);

  // --- REFS ---
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // 1. Initial Load: Get list, select most recent if available
  useEffect(() => {
    api.fetchChatList().then(chats => {
        if (chats.length > 0) {
            handleSelectChat(chats[0].chat_id);
        }
    });
  }, []);

  // 2. Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // =====================
  // SIDEBAR ACTIONS
  // =====================

  const handleSelectChat = async (id: string) => {
    setActiveChatId(id);
    const history = await api.fetchChatHistory(id);
    
    // Convert backend history to UI format
    const formatted: Message[] = history.map((h: any) => ({
        sender: h.role === "human" ? "user" : "jarvis",
        text: h.content
    }));
    
    setMessages(formatted);
  };

  const handleNewChat = async () => {
    const newChat = await api.createNewChat();
    setActiveChatId(newChat.chat_id);
    setMessages([]); // Clear chat window
    // Sidebar will auto-detect the ID change and refresh itself
  };

  // =====================
  // VOICE ENGINE
  // =====================

  const startRecording = async () => {
    try {
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
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Microphone access denied or not available.");
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  // =====================
  // MESSAGE PROCESSING
  // =====================

  const handleAudioSubmit = async (audioBlob: Blob) => {
    setIsProcessing(true);
    try {
      const text = await api.sendAudio(audioBlob);
      if (text) {
        addMessage("user", text);
        await processResponse(text);
      }
    } catch (error) {
      console.error("Error sending audio:", error);
    }
    setIsProcessing(false);
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;

    addMessage("user", textInput);
    setTextInput("");
    setIsProcessing(true);
    await processResponse(textInput);
    setIsProcessing(false);
  };

  const processResponse = async (text: string) => {
    try {
      // Send message to Brain
      const data = await api.sendMessage(text, activeChatId);
      
      // If Brain started a new conversation, update ID
      if (data.chat_id && data.chat_id !== activeChatId) {
          setActiveChatId(data.chat_id);
      }

      addMessage("jarvis", data.response);
      await playAudioResponse(data.response);

    } catch (error) {
      console.error("Error fetching chat response:", error);
      addMessage("jarvis", "I'm having trouble connecting to my brain right now.");
    }
  };

  // =====================
  // TTS & ANIMATION
  // =====================

  const playAudioResponse = async (text: string) => {
    if (!text) return;
    setIsSpeaking(true); 

    try {
        const res = await fetch("http://127.0.0.1:8000/tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);

        audio.onended = () => setIsSpeaking(false);
        await audio.play();
    } catch (e) {
        console.error("TTS Error", e);
        setIsSpeaking(false);
    }
  };

  const addMessage = (sender: "user" | "jarvis", text: string) => {
    setMessages((prev) => [...prev, { sender, text }]);
  };

  return (
    <div className="jarvis-container">
      {/* HEADER */}
      <h1 style={{ letterSpacing: "5px", textShadow: "0 0 10px red", zIndex: 10 }}>
        J.A.R.V.I.S
      </h1>

      {/* NEW SIDEBAR COMPONENT */}
      <Sidebar 
        isOpen={showSidebar}
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onClose={() => setShowSidebar(false)}
      />

      {/* ORB ANIMATION */}
      <div className="orb-container">
        <div className={`arc-reactor ${isRecording ? "listening" : ""} ${isProcessing ? "processing" : ""} ${isSpeaking ? "speaking" : ""}`} />
      </div>

      {/* CHAT WINDOW */}
      <div className="chat-window">
        {messages.length === 0 && (
          <div className="system-text">System Online. Awaiting Input...</div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.sender}`}>
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* INPUT AREA */}
      <form className="input-area" onSubmit={handleTextSubmit}>
        <input
          type="text"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Type a command..."
          disabled={isProcessing || isRecording}
        />
        <button type="submit" disabled={!textInput || isProcessing}>SEND</button>
        
        {/* MIC BUTTON */}
        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          className={isRecording ? "mic-active" : ""}
          disabled={isProcessing}
        >
          {isRecording ? "STOP" : "VOICE"}
        </button>

        {/* SIDEBAR TOGGLE */}
        <button 
            type="button" 
            onClick={() => setShowSidebar(!showSidebar)}
            style={{border: showSidebar ? '1px solid red' : '1px solid #333'}}
        >
          {showSidebar ? "HIDE" : "SHOW"}
        </button>
      </form>
    </div>
  );
}

export default App;