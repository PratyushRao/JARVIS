/* src/api.ts */

const API_BASE = "http://127.0.0.1:8000";

export interface ChatItem {
  chat_id: string;
  name: string;
}

export interface ChatMessage {
  role: "human" | "ai";
  content: string;
}

// --- MANAGEMENT ---

export const fetchChatList = async (): Promise<ChatItem[]> => {
  try {
    const res = await fetch(`${API_BASE}/chats`);
    return await res.json();
  } catch (e) {
    console.error("Failed to fetch chats:", e);
    return [];
  }
};

export const createNewChat = async (): Promise<ChatItem> => {
  const res = await fetch(`${API_BASE}/chats/new`, { method: "POST" });
  return await res.json();
};

export const fetchChatHistory = async (chatId: string): Promise<ChatMessage[]> => {
  const res = await fetch(`${API_BASE}/chats/${chatId}/history`);
  return await res.json();
};

export const deleteChat = async (chatId: string) => {
  await fetch(`${API_BASE}/chats/${chatId}`, { method: "DELETE" });
};

// --- CORE INTERACTION ---

export const sendMessage = async (text: string, chatId: string | null) => {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // FIX 1: Send "chatId" (camelCase) to match Backend Pydantic Alias
    body: JSON.stringify({ text, chatId: chatId }),
  });
  return await res.json();
};

// FIX 2: Added Missing TTS Function
export const playTTS = async (text: string) => {
  try {
    const res = await fetch(`${API_BASE}/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) throw new Error("TTS Generation failed");

    // Convert the response blob (audio file) into a playable URL
    const blob = await res.blob();
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    
    // Play immediately
    audio.play();
  } catch (e) {
    console.error("Audio Playback Error:", e);
  }
};

export const sendAudio = async (audioBlob: Blob): Promise<string> => {
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    const res = await fetch(`${API_BASE}/stt`, {
        method: "POST",
        body: formData, // No JSON headers for file upload
    });
    
    const data = await res.json();
    return data.text; 
}