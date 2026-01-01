import streamlit as st
import memory_manager as mem
import llm_services as brain

# Page Config
st.set_page_config(page_title="Jarvis AI", layout="wide")

# --- CSS for Sidebar Scroll & Layout ---
st.markdown("""
<style>
    /* Make the sidebar scrollable and look nicer */
    section[data-testid="stSidebar"] {
        overflow-y: auto;
    }
    .chat-btn {
        width: 100%;
        text-align: left;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "current_chat_id" not in st.session_state:
    # Create a default chat if none exists, or load the first one
    data = mem.load_data()
    if not data["chats"]:
        st.session_state["current_chat_id"] = mem.create_new_chat()
    else:
        # Load the most recent chat key
        st.session_state["current_chat_id"] = list(data["chats"].keys())[-1]

# --- SIDEBAR: Chat Management ---
with st.sidebar:
    st.title("🗂️ Chat History")
    
    # 1. New Chat Button
    if st.button("+ New Chat", use_container_width=True):
        new_id = mem.create_new_chat()
        st.session_state["current_chat_id"] = new_id
        st.rerun()

    st.markdown("---")

    # 2. List Existing Chats (Scrollable by default in Streamlit sidebar)
    data = mem.load_data()
    
    # We iterate in reverse to show newest first
    chat_ids = list(data["chats"].keys())[::-1]
    
    for chat_id in chat_ids:
        chat_name = data["chats"][chat_id]["name"]
        
        # Highlight the current chat
        button_type = "primary" if chat_id == st.session_state["current_chat_id"] else "secondary"
        
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(chat_name, key=chat_id, type=button_type, use_container_width=True):
                st.session_state["current_chat_id"] = chat_id
                st.rerun()
        with col2:
            # Delete button (small 'x')
            if st.button("✕", key=f"del_{chat_id}"):
                mem.delete_chat(chat_id)
                # If we deleted the active chat, reset to a new one
                if chat_id == st.session_state["current_chat_id"]:
                    st.session_state["current_chat_id"] = mem.create_new_chat()
                st.rerun()

    st.markdown("---")
    
    # 3. Rename Current Chat
    if st.session_state["current_chat_id"] in data["chats"]:
        current_name = data["chats"][st.session_state["current_chat_id"]]["name"]
        new_name = st.text_input("Rename Chat:", value=current_name)
        if new_name != current_name:
            mem.rename_chat(st.session_state["current_chat_id"], new_name)
            st.rerun()

    # 4. Long Term Memory Viewer (Optional Debug)
    with st.expander("🧠 Long-Term Memory"):
        ltm = mem.get_long_term_memory()
        st.write(ltm)
        if st.button("Clear LTM"):
            # You can implement a clear function in memory_manager if needed
            pass

# --- MAIN CHAT AREA ---

# Load history for the CURRENT chat ID
current_id = st.session_state["current_chat_id"]
history = mem.get_chat_history(current_id)
long_term_mem = mem.get_long_term_memory()

st.title(f"💬 {data['chats'][current_id]['name']}")

# Display Chat History
for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if user_input := st.chat_input("Say something..."):
    # 1. Display User Message
    with st.chat_message("human"):
        st.markdown(user_input)
    
    # 2. Add to History (File)
    mem.append_to_chat(current_id, "human", user_input)

    # 3. Get AI Response
    # Convert history dicts to format expected by LangChain if needed, 
    # or just pass the list of dicts if your prompt handles it.
    # Here we pass the raw text history for simplicity in context or formatted objects.
    
    # **Crucial:** We need to format the history for LangChain
    # LangChain expects (HumanMessage, AIMessage) objects, or strictly formatted list
    # For simplicity, we will pass the list and let the prompt handle structure or 
    # re-convert it here.
    
    from langchain_core.messages import HumanMessage, AIMessage
    langchain_history = []
    for h in history:
        if h["role"] == "human":
            langchain_history.append(HumanMessage(content=h["content"]))
        else:
            langchain_history.append(AIMessage(content=h["content"]))

    # Generate Response
    response_text = brain.get_brain_response(user_input, langchain_history, long_term_mem)

    # 4. Display AI Response
    with st.chat_message("ai"):
        st.markdown(response_text)

    # 5. Save AI Response
    mem.append_to_chat(current_id, "ai", response_text)

    # 6. (Optional) Auto-Memory Extraction
    # Simple logic: If user says "My name is...", save to LTM. 
    # A real implementation would use a separate LLM call to extract facts.
    if "my name is" in user_input.lower():
        name_fact = user_input  # In reality, you'd process this string
        mem.add_long_term_memory(f"User mention: {name_fact}")