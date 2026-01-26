import os
import pathlib
from dotenv import load_dotenv

# Try to load .env from repo root first
_repo_root = pathlib.Path(__file__).resolve().parents[2]
_dotenv_path = _repo_root / ".env"
if _dotenv_path.exists():
    load_dotenv(dotenv_path=str(_dotenv_path))
else:
    load_dotenv()

# --- IMPORTS ---
# Note: If Pylance complains, ensure you have run: 
# pip install langchain-groq langchain-core langchain-community
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# --- LOAD ENVIRONMENT VARIABLES ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class Brain:
    def __init__(self):
        # Initialize state; do NOT perform heavy network ops here without handling errors.
        self.llm = None
        self._init_error = None

        # Attempt to initialize the ChatGroq client only if the env var is present
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            self._init_error = "GROQ_API_KEY not set"
            return

        try:
            # 1. Initialize Groq (Llama 3.3 is very fast/smart)
            self.llm = ChatGroq(
                groq_api_key=groq_key,
                model_name="llama-3.3-70b-versatile",
                temperature=0.3,
            )

            # 2. UPDATED SYSTEM MESSAGE (The Fix)
            # This teaches Jarvis to output JSON when he needs to search
            self.system_message_text = (
                "You are J.A.R.V.I.S, a precise and intelligent AI assistant.\n\n"

                "LIMIT: Respond in at most 30 words.\n\n"

                "You have TWO tools:\n"
                "1) Web Search Tool → for real-time info\n"
                "2) Local Device Control Tool → for controlling the user's computer\n\n"

                "=========================\n"
                "WEB SEARCH TOOL\n"
                "Use when user asks about news, weather, live info, or unknown facts.\n"
                "FORMAT:\n"
                '{"query": "search text"}\n\n'

                "=========================\n"
                "LOCAL DEVICE CONTROL TOOL\n"
                "Use when user asks to open apps, websites, change volume, create files, shutdown, etc.\n"
                "FORMAT:\n"
                '{"action":"open_app","app":"notepad"}\n'
                '{"action":"open_website","url":"https://google.com"}\n'
                '{"action":"set_volume","level":50}\n'

                "When using a tool, OUTPUT ONLY the JSON. No explanation.\n"
                "If normal question → answer normally.\n"
            )


        except Exception as e:
            # Capture initialization errors and avoid raising during import
            self._init_error = str(e)

    def generate_response(self, user_text, chat_history=[], context=""):
        # 1. Convert Chat History
        formatted_history = []

        if context:
            formatted_history.append(SystemMessage(content=f"Long Term Memory Context: {context}"))

        for msg in chat_history:
            if isinstance(msg, dict):
                if msg.get('role') == 'human':
                    formatted_history.append(HumanMessage(content=msg.get('content')))
                else:
                    formatted_history.append(AIMessage(content=msg.get('content')))
            else:
                formatted_history.append(msg)

        try:
            # 2. Use LLM directly
            all_messages = [
                SystemMessage(content=self.system_message_text),
                *formatted_history,
                HumanMessage(content=user_text)
            ]

            response = self.llm.invoke(all_messages)
            return response.content

        except Exception as e:
            # Catch any unexpected error
            print(f"❌ generate_response error: {e}")
            return "I apologize, sir. My neural pathways failed to generate a response."

# Lazy Global Instance
_brain_instance = None


def _get_brain_instance():
    """Return a Brain instance, re-attempt initialization when a GROQ key becomes available."""
    global _brain_instance
    groq_key = os.getenv("GROQ_API_KEY")

    # If already initialized and healthy, return it
    if _brain_instance is not None and not getattr(_brain_instance, "_init_error", None):
        return _brain_instance

    # If we had a previous init error but a key is now present, reattempt
    if _brain_instance is not None and getattr(_brain_instance, "_init_error", None) and groq_key:
        try:
            _brain_instance = Brain()
            if getattr(_brain_instance, "_init_error", None):
                print(f"⚠️ Brain init warning on retry: {_brain_instance._init_error}")
                return None
            return _brain_instance
        except Exception as e:
            print(f"⚠️ Could not initialize Brain on retry: {e}")
            _brain_instance = None
            return None

    # If we have no key, do not attempt network init
    if not groq_key:
        return None

    # Last resort: try to initialize with a key present
    try:
        _brain_instance = Brain()
        if getattr(_brain_instance, "_init_error", None):
            print(f"⚠️ Brain init warning: {_brain_instance._init_error}")
            return None
        return _brain_instance
    except Exception as e:
        print(f"⚠️ Could not initialize Brain: {e}")
        _brain_instance = None
        return None


def get_brain_response(user_input: str, chat_history: list, long_term_memory: list):
    """High-level entrypoint for other modules."""
    # Go directly to the LLM
    memory_context = "\n".join([f"- {m}" for m in long_term_memory])
    inst = _get_brain_instance()
    if inst is None:
        return "I couldn't contact the language model right now; please try again later."
    resp = inst.generate_response(user_input, chat_history, memory_context)
    if not resp:
        return "I couldn't contact the language model right now; please try again later."
    return resp


# --- STATUS CHECK ---
def check_status() -> dict:
    """Return a lightweight status dict describing model availability."""
    # Local multimodal availability is cheap to check
    try:
        from backend.brain.local_multimodal import is_available as _local_avail
        local_ok = _local_avail()
    except Exception:
        local_ok = False

    # Captioner libraries present?
    captioner_libs = True
    try:
        import transformers  # noqa: F401
        import torch  # noqa: F401
    except Exception:
        captioner_libs = False

    return {
        "groq_key_present": bool(os.getenv("GROQ_API_KEY")),
        "brain_initialized": _brain_instance is not None,
        "brain_init_error": getattr(_brain_instance, "_init_error", None) if _brain_instance else None,
        "llm_available": (_brain_instance is not None and getattr(_brain_instance, "_init_error", None) is None),
        "local_multimodal_available": local_ok,
        "captioner_libraries_present": captioner_libs,
    }