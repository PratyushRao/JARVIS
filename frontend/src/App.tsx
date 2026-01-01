/* src/App.tsx */
import { useRef, useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import * as api from "./api"; // <--- Import our new helper
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
  
  // Sidebar State
  const [showSidebar, setShowSidebar] = useState(false);
  const [chatList, setChatList] = useState<api.ChatItem[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const audioQueueRef = useRef<string[]>([]);
  const isPlayingRef = useRef(false);

  // 1. Load Chats on Startup
  useEffect(() => {
    loadSidebar();
  }, []);

  // Auto scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // =====================
  // SIDEBAR FUNCTIONS
  // =====================

  const loadSidebar = async () => {
    const chats = await api.fetchChatList();
    setChatList(chats);
    
    // Select most recent chat if none selected
    if (chats.length > 0 && !activeChatId) {
       selectChat(chats[0].chat_id);
    }
  };

  const selectChat = async (id: string) => {
    setActiveChatId(id);
    const history = await api.fetchChatHistory(id);
    
    // Map backend format (human/ai) to frontend format (user/jarvis)
    const formatted: Message[] = history.map((h) => ({
        sender: h.role === "human" ? "user" : "jarvis",
        text: h.content
    }));
    
    setMessages(formatted);
  };

  const handleNewChat = async () => {
    const newChat = await api.createNewChat();
    setChatList([newChat, ...chatList]);
    setActiveChatId(newChat.chat_id);
    setMessages([]); // Clear screen for new chat
  };

  const handleDeleteChat = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent clicking the parent div
    await api.deleteChat(id);
    setChatList(chatList.filter(c => c.chat_id !== id));
    
    if (id === activeChatId) {
        setMessages([]);
        setActiveChatId(null);
    }
  };

  // =====================
  // VOICE RECORDING
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
  // AUDIO SUBMIT
  // =====================

  const handleAudioSubmit = async (audioBlob: Blob) => {
    setIsProcessing(true);

    const formData = new FormData();
    formData.append("file", audioBlob, "speech.webm");

    try {
      // 1. Get Text from Speech
      const res = await fetch("http://127.0.0.1:8000/stt", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data.text) {
        addMessage("user", data.text);
        // 2. Process via Brain
        await processResponse(data.text);
      }
    } catch (error) {
      console.error("Error sending audio:", error);
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
  // LLM LOGIC (Updated to use API)
  // =====================

  const processResponse = async (text: string) => {
    try {
      // Use our new API helper so it sends the chat_id
      const data = await api.sendMessage(text, activeChatId);
      
      // If backend created a new ID (for first msg), update state
      if (data.chat_id && data.chat_id !== activeChatId) {
          setActiveChatId(data.chat_id);
          // Refresh list to show new name
          loadSidebar();
      }

      addMessage("jarvis", data.response);
      await speakText(data.response);
    } catch (error) {
      console.error("Error fetching chat response:", error);
      addMessage("jarvis", "I'm having trouble connecting to my brain right now.");
    }
  };

  // =====================
  // TTS (Sentence Queueing)
  // =====================

  const playNextInQueue = () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setIsSpeaking(false);
      return;
    }

    isPlayingRef.current = true;
    setIsSpeaking(true);

    const nextAudioUrl = audioQueueRef.current.shift(); // Take first item

    if (audioPlayerRef.current && nextAudioUrl) {
      audioPlayerRef.current.src = nextAudioUrl;
      audioPlayerRef.current.play();
      audioPlayerRef.current.onended = playNextInQueue;
    }
  };

  const speakText = async (text: string) => {
    if (!text) return;

    const sentences = text.match(/[^\.!\?]+[\.!\?]+/g) || [text];

    for (const sentence of sentences) {
      try {
        const res = await fetch(
          `http://127.0.0.1:8000/tts?text=${encodeURIComponent(sentence)}`,
          { method: "POST" }
        );

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        audioQueueRef.current.push(url);

        if (!isPlayingRef.current) {
          playNextInQueue();
        }
      } catch (error) {
        console.error("Error generating speech segment:", error);
      }
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

      {/* SIDEBAR OVERLAY */}
      {showSidebar && (
        <div style={{
            position: 'absolute', top: 0, left: 0, bottom: 0, width: '250px',
            background: 'rgba(10, 10, 10, 0.95)', borderRight: '1px solid #ff0000',
            zIndex: 100, padding: '20px', overflowY: 'auto', backdropFilter: 'blur(5px)'
        }}>
            <h3 style={{color: 'red', borderBottom: '1px solid red', paddingBottom: '10px'}}>MEMORY</h3>
            <button 
                onClick={handleNewChat} 
                style={{width: '100%', marginBottom: '20px', background: 'rgba(255,0,0,0.2)', border: '1px solid red', color: 'white'}}
            >
                + NEW OPERATION
            </button>
            
            {chatList.map(chat => (
                <div key={chat.chat_id} 
                    onClick={() => selectChat(chat.chat_id)}
                    style={{
                        padding: '10px', 
                        marginBottom: '5px',
                        cursor: 'pointer',
                        background: activeChatId === chat.chat_id ? 'rgba(255, 0, 0, 0.3)' : 'transparent',
                        border: '1px solid ' + (activeChatId === chat.chat_id ? 'red' : 'transparent'),
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                    }}
                >
                    <span style={{fontSize: '0.9rem', color: '#ccc'}}>{chat.name}</span>
                    <span 
                        onClick={(e) => handleDeleteChat(chat.chat_id, e)}
                        style={{color: 'red', fontWeight: 'bold', cursor: 'pointer', marginLeft: '10px'}}
                    >
                        ×
                    </span>
                </div>
            ))}
        </div>
      )}

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
            <ReactMarkdown>{msg.text}</ReactMarkdown>
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

        {/* 👇 THIS IS NOW THE SIDEBAR TOGGLE */}
        <button 
            type="button" 
            onClick={() => setShowSidebar(!showSidebar)}
            style={{border: showSidebar ? '1px solid red' : '1px solid #333'}}
        >
          {showSidebar ? "HIDE" : "SHOW"}
        </button>
      </form>

      <audio ref={audioPlayerRef} hidden />
    </div>
  );
}

export default App;