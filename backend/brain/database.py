import json
import os
import uuid
from datetime import datetime

# --- CONFIGURATION ---
CHATS_FILE = "data/chats.json"
MEMORY_FILE = "data/memory.json"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# --- INITIALIZE FILES ---
def init_db():
    if not os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "w") as f:
            json.dump({}, f)
    
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w") as f:
            json.dump([], f) # List of memory strings

# --- CHAT MANAGEMENT ---
def get_all_chats():
    """Returns a list of all chat sessions with their IDs and Titles."""
    init_db()
    try:
        with open(CHATS_FILE, "r") as f:
            data = json.load(f)
            # Return list of {id, title, timestamp}
            chat_list = []
            for chat_id, chat_data in data.items():
                chat_list.append({
                    "id": chat_id,
                    "title": chat_data.get("title", "New Conversation"),
                    "created_at": chat_data.get("created_at", "")
                })
            # Sort by newest first (optional)
            return chat_list
    except:
        return []

def get_chat_history(chat_id):
    init_db()
    with open(CHATS_FILE, "r") as f:
        data = json.load(f)
        return data.get(chat_id, {}).get("messages", [])

def create_chat(title="New Conversation"):
    init_db()
    chat_id = str(uuid.uuid4().hex)
    new_chat = {
        "title": title,
        "created_at": str(datetime.now()),
        "messages": []
    }
    
    with open(CHATS_FILE, "r+") as f:
        data = json.load(f)
        data[chat_id] = new_chat
        f.seek(0)
        json.dump(data, f, indent=4)
        
    return chat_id

def save_message(chat_id, role, content):
    """Saves a single message to a specific chat."""
    init_db()
    with open(CHATS_FILE, "r+") as f:
        data = json.load(f)
        
        if chat_id not in data:
            # If chat doesn't exist, create it locally in memory first
            data[chat_id] = {
                "title": "New Conversation", 
                "created_at": str(datetime.now()), 
                "messages": []
            }
            
        data[chat_id]["messages"].append({"role": role, "content": content})
        
        f.seek(0)
        json.dump(data, f, indent=4)

def rename_chat(chat_id, new_title):
    """Renames a specific chat."""
    init_db()
    with open(CHATS_FILE, "r+") as f:
        data = json.load(f)
        if chat_id in data:
            data[chat_id]["title"] = new_title
            f.seek(0)
            json.dump(data, f, indent=4)
            return True
        return False

# --- LONG TERM MEMORY ---
def get_long_term_memory():
    """Returns the list of core memories."""
    init_db()
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def add_long_term_memory(memory_text):
    """Adds a new fact to long term memory."""
    init_db()
    with open(MEMORY_FILE, "r+") as f:
        memories = json.load(f)
        if memory_text not in memories:
            memories.append(memory_text)
            f.seek(0)
            json.dump(memories, f, indent=4)