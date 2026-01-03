import sys
import os
from PIL import Image

# 1. DISABLE LOGS (Keeps terminal clean)
os.environ["LLAMA_CPP_LIB_VERBOSE"] = "0"

try:
    from llama_cpp import Llama
    from llama_cpp.llama_chat_format import Llava15ChatHandler
except ImportError:
    print("Error: Library not found.")
    print("Run: pip install llama-cpp-python pillow")
    sys.exit(1)

def setup_model():
    """
    Loads the BakLLaVA (Mistral v1.5) model specifically for your screenshot files.
    """
    # --- EXACT FILENAMES FROM YOUR SCREENSHOT ---
    model_path = "./models/BakLLaVA1-MistralLLaVA-7B.q5_K_M.gguf"
    clip_path = "./models/BakLLaVA1-clip-mmproj-model-f16.gguf"

    # Verify files exist
    if not os.path.exists(model_path):
        print(f"\nERROR: Main model not found!")
        print(f"Expected location: {os.path.abspath(model_path)}")
        sys.exit(1)
        
    if not os.path.exists(clip_path):
        print(f"\nERROR: Clip model not found!")
        print(f"Expected location: {os.path.abspath(clip_path)}")
        sys.exit(1)

    print("Loading Model... (This takes about 5-10 seconds)")
    
    # Load the "Eyes" (CLIP)
    chat_handler = Llava15ChatHandler(clip_model_path=clip_path)

    # Load the "Brain" (Mistral)
    llm = Llama(
        model_path=model_path,
        chat_handler=chat_handler,
        n_ctx=2048,      # BakLLaVA uses 2048 context (Fast)
        n_batch=512,     # Process image in chunks
        n_gpu_layers=0,  # Force CPU
        verbose=False
    )
    return llm

def analyze_image(llm, image_uri, user_query):
    """
    Sends the image and text to the model.
    """
    try:
        output = llm.create_chat_completion(
            messages=[
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": image_uri}},
                    {"type": "text", "text": user_query}
                ]}
            ],
            max_tokens=150,  # Limit response size for speed
            temperature=0.1  # Keep it factual
        )
        return output["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error during analysis: {str(e)}"

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    
    # 1. Initialize Model
    model = setup_model()

    # 2. Locate Image
    current_dir = os.path.dirname(os.path.abspath(__file__))
    original_img_path = os.path.join(current_dir, "image2.jpg")
    
    if not os.path.exists(original_img_path):
        print(f"\nERROR: 'image2.jpg' not found in {current_dir}")
        sys.exit(1)

    # 3. OPTIMIZE IMAGE (Resize to 336x336 for speed)
    print("Processing image...")
    temp_img_path = os.path.join(current_dir, "temp_bakllava.jpg")
    
    try:
        with Image.open(original_img_path) as img:
            img = img.convert("RGB") # Handle PNG/Transparency issues
            img.thumbnail((336, 336)) # BakLLaVA native resolution
            img.save(temp_img_path)
            
        # Convert to standard URI format: file:///C:/Path/To/Image.jpg
        # Replace backslashes with forward slashes for Windows compatibility
        final_image_uri = f"file:///{temp_img_path.replace(os.sep, '/')}"
        
    except Exception as e:
        print(f"Error processing image file: {e}")
        sys.exit(1)

    # 4. Run Inference
    query = "How many kids are here?"
    print(f"Analyzing: {final_image_uri}")
    
    result = analyze_image(model, final_image_uri, query)
    
    print("\n" + "="*30)
    print(" MODEL ANSWER:")
    print("="*30)
    print(result)
    print("="*30)

    # Optional: Clean up temp file
    if os.path.exists(temp_img_path):
        os.remove(temp_img_path)