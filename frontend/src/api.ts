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

export const fetchChatList = async (): Promise<ChatItem[]> => {
  try {
    const res = await fetch(`${API_BASE}/chats`);
    return await res.json();
  } catch (e) {
    console.error(e);
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

export const sendMessage = async (text: string, chatId: string | null) => {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, chat_id: chatId }),
  });
  return await res.json();
};

export const deleteChat = async (chatId: string) => {
  await fetch(`${API_BASE}/chats/${chatId}`, { method: "DELETE" });
};