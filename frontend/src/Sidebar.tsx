import React, { useState, useEffect, useRef } from 'react';
import * as api from './api';
import { MoreVertical, Trash2, Edit2, MessageSquare, Check, X, Plus } from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onClose: () => void;
}

export default function Sidebar({ isOpen, activeChatId, onSelectChat, onNewChat, onClose }: SidebarProps) {
  // Use 'any' here to avoid strict interface issues for now, or import ChatItem from api
  const [chats, setChats] = useState<any[]>([]);
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  
  const menuRef = useRef<HTMLDivElement>(null);

  const loadChats = async () => {
    try {
      const data = await api.fetchChatList();
      setChats(data);
    } catch (e) {
      console.error("Sidebar load error", e);
    }
  };

  useEffect(() => {
    if (isOpen) loadChats();
  }, [isOpen, activeChatId]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpenId(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const startRenaming = (chat: any) => {
    setEditingChatId(chat.chat_id); // <--- FIXED
    setEditName(chat.name);
    setMenuOpenId(null);
  };

  const saveRename = async (chatId: string) => {
    if (!editName.trim()) return;
    await api.renameChat(chatId, editName);
    setEditingChatId(null);
    loadChats();
  };

  const handleDelete = async (chatId: string) => {
    if (confirm("Are you sure you want to delete this memory?")) {
      await api.deleteChat(chatId);
      if (chatId === activeChatId) onNewChat();
      loadChats();
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
        position: 'absolute', top: 0, left: 0, bottom: 0, width: '280px',
        background: 'rgba(10, 10, 10, 0.95)', borderRight: '1px solid #ff0000',
        zIndex: 100, display: 'flex', flexDirection: 'column', backdropFilter: 'blur(10px)',
        boxShadow: '5px 0 15px rgba(0,0,0,0.5)'
    }}>
      <div style={{ padding: '20px', borderBottom: '1px solid #333' }}>
        <h3 style={{ color: 'red', margin: '0 0 15px 0', letterSpacing: '2px', fontSize: '1.2rem' }}>MEMORY CORE</h3>
        <button 
          onClick={onNewChat}
          style={{
            width: '100%', padding: '12px', background: 'rgba(255, 0, 0, 0.1)', 
            border: '1px solid red', color: 'white', cursor: 'pointer', display: 'flex', 
            justifyContent: 'center', alignItems: 'center', gap: '10px', fontWeight: 'bold'
          }}
        >
          <Plus size={16} /> NEW OPERATION
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
        {chats.map((chat) => (
          <div 
            key={chat.chat_id} // <--- FIXED
            onClick={() => onSelectChat(chat.chat_id)} // <--- FIXED
            style={{
              position: 'relative',
              padding: '12px',
              marginBottom: '8px',
              borderRadius: '6px',
              cursor: 'pointer',
              background: activeChatId === chat.chat_id ? 'rgba(255, 0, 0, 0.2)' : 'transparent', // <--- FIXED
              border: activeChatId === chat.chat_id ? '1px solid red' : '1px solid transparent', // <--- FIXED
              display: 'flex', alignItems: 'center', gap: '10px', color: '#ccc',
              transition: 'all 0.2s ease'
            }}
          >
            <MessageSquare size={16} color={activeChatId === chat.chat_id ? 'red' : '#555'} />

            {editingChatId === chat.chat_id ? ( // <--- FIXED
              <div style={{ display: 'flex', flex: 1, gap: '5px' }} onClick={e => e.stopPropagation()}>
                <input 
                  autoFocus
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && saveRename(chat.chat_id)} // <--- FIXED
                  style={{ width: '100%', background: '#222', border: '1px solid #00aaff', color: 'white', padding: '4px', fontSize: '0.9rem' }}
                />
                <Check size={18} className="text-green-500 hover:text-green-400" onClick={() => saveRename(chat.chat_id)} />
                <X size={18} className="text-red-500 hover:text-red-400" onClick={() => setEditingChatId(null)} />
              </div>
            ) : (
              <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '0.9rem' }}>
                {chat.name || "New Chat"}
              </span>
            )}

            <div 
              onClick={(e) => { e.stopPropagation(); setMenuOpenId(menuOpenId === chat.chat_id ? null : chat.chat_id); }} // <--- FIXED
              style={{ padding: '4px' }}
            >
               <MoreVertical size={16} style={{ opacity: 0.7, cursor: 'pointer' }} />
            </div>

            {menuOpenId === chat.chat_id && ( // <--- FIXED
              <div ref={menuRef} style={{
                position: 'absolute', right: '10px', top: '40px',
                background: '#1a1a1a', border: '1px solid #444', borderRadius: '4px',
                zIndex: 999, boxShadow: '0 4px 15px rgba(0,0,0,0.8)', minWidth: '140px'
              }}>
                <div 
                  onClick={(e) => { e.stopPropagation(); startRenaming(chat); }}
                  style={{ padding: '10px 15px', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', color: '#ccc', fontSize: '0.85rem' }}
                >
                  <Edit2 size={14} /> Rename
                </div>
                <div 
                  onClick={(e) => { e.stopPropagation(); handleDelete(chat.chat_id); }} // <--- FIXED
                  style={{ padding: '10px 15px', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', color: '#ff4444', fontSize: '0.85rem', borderTop: '1px solid #333' }}
                >
                  <Trash2 size={14} /> Delete
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ padding: '20px', borderTop: '1px solid #333' }}>
         <button onClick={onClose} style={{ width: '100%', background: 'transparent', border: '1px solid #555', padding: '8px', color: '#888', cursor: 'pointer' }}>
           CLOSE PANEL
         </button>
      </div>
    </div>
  );
}