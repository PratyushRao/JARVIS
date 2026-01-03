import json
import os
import uuid
from datetime import datetime

# --- CONFIGURATION ---
DATA_DIR = "data"
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# --- INITIALIZE FILES ---
def init_db():
    if not os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "w") as f:
            json.dump({}, f)
    
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w") as f:
            json.dump([], f)

# --- CHAT FUNCTIONS (Matches main.py calls) ---

def get_all_chats():
    """Returns [{chat_id, name, timestamp}] for the sidebar."""
    init_db()
    try:
        with open(CHATS_FILE, "r") as f:
            data = json.load(f)
        
        chat_list = []
        for chat_id, chat_data in data.items():
            chat_list.append({
                "chat_id": chat_id,  # <--- CHANGED FROM "id" TO "chat_id"
                "name": chat_data.get("title", "New Conversation"),
                "timestamp": chat_data.get("created_at", "")
            })
        
        # Sort by newest first
        chat_list.sort(key=lambda x: x["timestamp"], reverse=True)
        return chat_list
    except:
        return []

def create_new_chat():
    """Creates a new chat and returns {chat_id, name}."""
    init_db()
    chat_id = uuid.uuid4().hex
    timestamp = datetime.now().isoformat()
    title = "New Conversation"
    
    new_chat = {
        "title": title,
        "created_at": timestamp,
        "messages": []
    }
    
    with open(CHATS_FILE, "r+") as f:
        data = json.load(f)
        data[chat_id] = new_chat
        f.seek(0)
        json.dump(data, f, indent=4)
        
    return {"chat_id": chat_id, "name": title}

def rename_chat(chat_id, new_name):
    """Renames a specific chat. Called by main.py endpoint."""
    init_db()
    try:
        with open(CHATS_FILE, "r+") as f:
            data = json.load(f)
            if chat_id in data:
                data[chat_id]["title"] = new_name
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                return True
    except:
        pass
    return False

def delete_chat(chat_id):
    """Deletes a chat."""
    init_db()
    try:
        with open(CHATS_FILE, "r+") as f:
            data = json.load(f)
            if chat_id in data:
                del data[chat_id]
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                return True
    except:
        pass
    return False

def get_chat_history(chat_id):
    """Returns list of message dicts."""
    init_db()
    try:
        with open(CHATS_FILE, "r") as f:
            data = json.load(f)
            return data.get(chat_id, {}).get("messages", [])
    except:
        return []

def append_to_chat(chat_id, role, content):
    """Saves a message to the JSON file."""
    init_db()
    try:
        with open(CHATS_FILE, "r+") as f:
            data = json.load(f)
            if chat_id in data:
                data[chat_id]["messages"].append({"role": role, "content": content})
                f.seek(0)
                json.dump(data, f, indent=4)
    except:
        pass

# --- MEMORY FUNCTIONS ---

def get_long_term_memory():
    """Returns list of memory strings."""
    init_db()
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def add_long_term_memory(memory_text):
    """Adds a new string to memory.json."""
    init_db()
    try:
        with open(MEMORY_FILE, "r+") as f:
            memories = json.load(f)
            if memory_text not in memories:
                memories.append(memory_text)
                f.seek(0)
                json.dump(memories, f, indent=4)
    except:
        pass