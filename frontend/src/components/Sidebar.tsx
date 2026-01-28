import { useState, useEffect, useRef } from 'react';
import * as api from '../api';
import {
  MoreVertical,
  Trash2,
  Edit2,
  MessageSquare,
  Check,
  X,
  Plus
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onClose: () => void;
}

interface Chat {
  chat_id: string;
  name?: string;
}

export default function Sidebar({
  isOpen,
  activeChatId,
  onSelectChat,
  onNewChat,
  onClose
}: SidebarProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  const menuRef = useRef<HTMLDivElement>(null);

  // Fetch chats
  useEffect(() => {
    if (!isOpen) return;
    api.fetchChatList().then(setChats).catch(console.error);
  }, [isOpen, activeChatId]);

  // Close menu on outside click
  useEffect(() => {
    const closeMenu = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpenId(null);
      }
    };
    document.addEventListener('mousedown', closeMenu);
    return () => document.removeEventListener('mousedown', closeMenu);
  }, []);

  // Parallax effect
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const x = (e.clientX - width / 2) / width; // -0.5 to 0.5
      const y = (e.clientY - height / 2) / height; // -0.5 to 0.5
      setTilt({ x, y });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const startRename = (chat: Chat) => {
    setEditingChatId(chat.chat_id);
    setEditName(chat.name || '');
    setMenuOpenId(null);
  };

  const saveRename = async (chatId: string) => {
    if (!editName.trim()) return;
    await api.renameChat(chatId, editName);
    setEditingChatId(null);
    setChats(await api.fetchChatList());
  };

  const deleteChat = async (chatId: string) => {
    if (!confirm('Delete this conversation?')) return;
    await api.deleteChat(chatId);
    if (chatId === activeChatId) onNewChat();
    setChats(await api.fetchChatList());
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        bottom: 0,
        width: '380px',
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(10,20,25,0.75)',
        backdropFilter: 'blur(16px) saturate(140%)',
        WebkitBackdropFilter: 'blur(16px) saturate(140%)',
        borderRight: '1px solid rgba(0,255,255,0.25)',
        boxShadow: '6px 0 30px rgba(0,255,255,0.08)',
        zIndex: 100,
        transform: `rotateY(${tilt.x * 5}deg) rotateX(${-tilt.y * 5}deg)`,
        transformStyle: 'preserve-3d',
        transition: 'transform 0.1s ease-out'
      }}
    >
      {/* subtle glass reflection */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background:
            'linear-gradient(180deg, rgba(255,255,255,0.06), transparent 40%, transparent 60%, rgba(255,255,255,0.03))'
        }}
      />

      {/* HEADER */}
      <div
        style={{
          padding: '20px',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          zIndex: 1
        }}
      >
        <h3
          style={{
            margin: '0 0 15px',
            letterSpacing: '3px',
            fontSize: '1.1rem',
            color: '#bffcff',
            textShadow: '0 0 8px rgba(0,255,255,0.35)'
          }}
        >
          MEMORY CORE
        </h3>

        <button
          onClick={onNewChat}
          style={{
            width: '100%',
            padding: '12px',
            background: 'rgba(0,255,255,0.08)',
            border: '1px solid rgba(0,255,255,0.35)',
            borderRadius: '8px',
            color: '#e8ffff',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '10px',
            fontWeight: 600,
            letterSpacing: '1px'
          }}
        >
          <Plus size={16} /> NEW OPERATION
        </button>
      </div>

      {/* CHAT LIST — ONLY THIS SCROLLS */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: '12px'
        }}
      >
        {chats.map(chat => (
          <div
            key={chat.chat_id}
            onClick={() => onSelectChat(chat.chat_id)}
            style={{
              position: 'relative',
              padding: '12px',
              marginBottom: '10px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              cursor: 'pointer',
              background:
                activeChatId === chat.chat_id
                  ? 'rgba(0,255,255,0.14)'
                  : 'rgba(255,255,255,0.03)',
              border:
                activeChatId === chat.chat_id
                  ? '1px solid rgba(0,255,255,0.45)'
                  : '1px solid rgba(255,255,255,0.05)',
              color: '#cfeff3',
              transform: `translateZ(${tilt.x * 5}px) translateY(${tilt.y * 5}px)`,
              transition: 'transform 0.1s ease-out'
            }}
          >
            <MessageSquare size={16} />

            {editingChatId === chat.chat_id ? (
              <div
                style={{ display: 'flex', flex: 1, gap: '6px' }}
                onClick={e => e.stopPropagation()}
              >
                <input
                  autoFocus
                  value={editName}
                  onChange={e => setEditName(e.target.value)}
                  onKeyDown={e =>
                    e.key === 'Enter' && saveRename(chat.chat_id)
                  }
                  style={{
                    flex: 1,
                    background: 'rgba(0,0,0,0.6)',
                    border: '1px solid rgba(0,255,255,0.6)',
                    color: '#fff',
                    padding: '4px'
                  }}
                />
                <Check size={18} color="#7fffd4" />
                <X
                  size={18}
                  color="#ff9999"
                  onClick={() => setEditingChatId(null)}
                />
              </div>
            ) : (
              <span
                style={{
                  flex: 1,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {chat.name || 'New Chat'}
              </span>
            )}

            <div
              onClick={e => {
                e.stopPropagation();
                setMenuOpenId(
                  menuOpenId === chat.chat_id ? null : chat.chat_id
                );
              }}
            >
              <MoreVertical size={16} />
            </div>

            {menuOpenId === chat.chat_id && (
              <div
                ref={menuRef}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '42px',
                  background: 'rgba(15,25,30,0.9)',
                  backdropFilter: 'blur(12px)',
                  border: '1px solid rgba(0,255,255,0.25)',
                  borderRadius: '6px',
                  minWidth: '140px'
                }}
              >
                <div
                  onClick={() => startRename(chat)}
                  style={{
                    padding: '10px',
                    cursor: 'pointer',
                    display: 'flex',
                    gap: '8px'
                  }}
                >
                  <Edit2 size={14} /> Rename
                </div>
                <div
                  onClick={() => deleteChat(chat.chat_id)}
                  style={{
                    padding: '10px',
                    cursor: 'pointer',
                    display: 'flex',
                    gap: '8px',
                    color: '#ffaaaa'
                  }}
                >
                  <Trash2 size={14} /> Delete
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* FOOTER — FIXED */}
      <div
        style={{
          padding: '20px',
          borderTop: '1px solid rgba(255,255,255,0.08)'
        }}
      >
        <button
          onClick={onClose}
          style={{
            width: '100%',
            padding: '12px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.15)',
            borderRadius: '8px',
            color: '#aacfd6'
          }}
        >
          CLOSE PANEL
        </button>
      </div>
    </div>
  );
}
