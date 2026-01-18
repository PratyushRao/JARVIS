import os
import tempfile
from typing import Tuple, Optional

# Singleton holder for the local multimodal model
_MODEL = None
_AVAILABLE = None

# Default model locations (relative to repo root)
BASE_MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Kavish_image_captioning", "models"))
# Allow overriding model paths via environment variables for flexibility during testing
DEFAULT_MODEL_PATH = os.getenv("LOCAL_BAKLLAVA_MODEL_PATH") or os.path.join(BASE_MODELS_DIR, "BakLLaVA1-MistralLLaVA-7B.q5_K_M.gguf")
DEFAULT_CLIP_PATH = os.getenv("LOCAL_CLIP_MODEL_PATH") or os.path.join(BASE_MODELS_DIR, "BakLLaVA1-clip-mmproj-model-f16.gguf")


def is_available() -> bool:
    """Return True if a local llama-cpp multimodal setup is available."""
    global _AVAILABLE
    if _AVAILABLE is not None:
        return _AVAILABLE

    try:
        import llama_cpp  # noqa: F401
        # check files exist
        if os.path.exists(DEFAULT_MODEL_PATH) and os.path.exists(DEFAULT_CLIP_PATH):
            _AVAILABLE = True
        else:
            _AVAILABLE = False
    except Exception:
        _AVAILABLE = False

    return _AVAILABLE


def _init_model():
    """Initialize and cache the llama-cpp model and chat handler."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    try:
        from llama_cpp import Llama
        from llama_cpp.llama_chat_format import Llava15ChatHandler

        chat_handler = Llava15ChatHandler(clip_model_path=DEFAULT_CLIP_PATH)
        llm = Llama(
            model_path=DEFAULT_MODEL_PATH,
            chat_handler=chat_handler,
            n_ctx=1024,  # Reduced for faster processing
            n_batch=256,  # Smaller batch
            n_gpu_layers=0,
            verbose=False,
            n_threads=4,  # Use multiple CPU threads
        )

        _MODEL = (llm, chat_handler)
        return _MODEL
    except Exception as e:
        _MODEL = None
        raise e


def analyze_image_with_local_llm(image_bytes: bytes, question: str) -> Tuple[Optional[str], Optional[str]]:
    """Send the image + question to the local multimodal LLM and return (answer, error).

    This writes the image to a temp file and uses a file:// URI for the chat handler.
    """
    if not is_available():
        return None, "local multimodal LLM not available"

    try:
        model, _ = _init_model()
        # write to temp file
        fd, path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        with open(path, "wb") as f:
            f.write(image_bytes)

        image_uri = f"file:///{path.replace(os.sep, '/')}"

        res = model.create_chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_uri}},
                        {"type": "text", "text": question},
                    ],
                }
            ],
            max_tokens=200,
            temperature=0.1,
        )

        # Try to extract the assistant content
        answer = None
        try:
            answer = res["choices"][0]["message"]["content"]
        except Exception:
            # Some llama-cpp versions return strings directly
            if isinstance(res, dict) and "choices" in res:
                c = res["choices"][0]
                if isinstance(c, dict):
                    answer = c.get("message", {}).get("content") or str(res)
            else:
                answer = str(res)

        # Clean up temp file
        try:
            os.remove(path)
        except Exception:
            pass

        return answer, None
    except Exception as e:
        return None, str(e)
