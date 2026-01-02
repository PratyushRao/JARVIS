/* src/App.tsx */
import { useRef, useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import * as api from "./api"; 
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
  const chatEndRef = useRef<HTMLDivElement | null>(null);

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
    setMessages([]); 
  };

  const handleDeleteChat = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation(); 
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

    try {
      // FIX 1: Use the api.ts helper we created
      const text = await api.sendAudio(audioBlob);

      if (text) {
        addMessage("user", text);
        // Pass text to brain
        await processResponse(text);
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
    setTextInput("");
    setIsProcessing(true);
    await processResponse(textInput);
    setIsProcessing(false);
  };

  // =====================
  // LLM LOGIC
  // =====================

  const processResponse = async (text: string) => {
    try {
      // FIX 2: Send activeChatId so backend knows context
      const data = await api.sendMessage(text, activeChatId);
      
      // Update ID if backend assigned a new one
      if (data.chat_id && data.chat_id !== activeChatId) {
          setActiveChatId(data.chat_id);
          loadSidebar();
      }

      addMessage("jarvis", data.response);
      
      // FIX 3: Trigger TTS with animation state
      await playAudioResponse(data.response);

    } catch (error) {
      console.error("Error fetching chat response:", error);
      addMessage("jarvis", "I'm having trouble connecting to my brain right now.");
    }
  };

  // =====================
  // TTS (Animation Linked)
  // =====================

  const playAudioResponse = async (text: string) => {
    if (!text) return;

    setIsSpeaking(true); // START ANIMATION

    try {
        // FIX 4: Correct fetch to new JSON endpoint
        const res = await fetch("http://127.0.0.1:8000/tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);

        // When audio ends, STOP ANIMATION
        audio.onended = () => {
            setIsSpeaking(false);
        };

        await audio.play();
    } catch (e) {
        console.error("TTS Error", e);
        setIsSpeaking(false); // Stop if error
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