import json
import os
import uuid
from datetime import datetime

DB_FILE = "chat_data.json"

def load_data():
    if not os.path.exists(DB_FILE):
        return {"chats": {}, "long_term_memory": []}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {"chats": {}, "long_term_memory": []}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- CRUD OPERATIONS FOR FRONTEND ---

def create_new_chat():
    data = load_data()
    chat_id = uuid.uuid4().hex
    chat_name = f"New Chat {datetime.now().strftime('%H:%M')}"
    data["chats"][chat_id] = {"name": chat_name, "history": []}
    save_data(data)
    return {"chat_id": chat_id, "name": chat_name}

def get_all_chats():
    data = load_data()
    # Return list of {id, name} sorted by newest first
    # We assume keys are added in order, or we can rely on file order.
    # Python dicts preserve insertion order in 3.7+
    chats_list = [{"chat_id": k, "name": v["name"]} for k, v in data["chats"].items()]
    return chats_list[::-1]  # Reverse to show newest on top

def rename_chat(chat_id, new_name):
    data = load_data()
    if chat_id in data["chats"]:
        data["chats"][chat_id]["name"] = new_name
        save_data(data)
        return True
    return False

def delete_chat(chat_id):
    data = load_data()
    if chat_id in data["chats"]:
        del data["chats"][chat_id]
        save_data(data)
        return True
    return False

def get_chat_history(chat_id):
    data = load_data()
    return data["chats"].get(chat_id, {}).get("history", [])

def append_to_chat(chat_id, role, content):
    data = load_data()
    if chat_id in data["chats"]:
        data["chats"][chat_id]["history"].append({"role": role, "content": content})
        save_data(data)

def get_long_term_memory():
    data = load_data()
    return data.get("long_term_memory", [])

def add_long_term_memory(fact):
    data = load_data()
    if fact not in data["long_term_memory"]:
        data["long_term_memory"].append(fact)
        save_data(data)