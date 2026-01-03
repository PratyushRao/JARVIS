import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from brain.web_search import search_duckduckgo

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

class Brain:
    def __init__(self):
        # 1. Initialize Mistral
        self.llm = ChatMistralAI(
            mistral_api_key=MISTRAL_API_KEY,
            model="mistral-small-latest",
            temperature=0.3
        )
        
        # 2. Bind the Tool DIRECTLY to the Model
        self.llm_with_tools = self.llm.bind_tools(
            [search_duckduckgo],
            tool_choice="auto"
        )

        # 3. Define Personality
        self.system_prompt = (
            "You are J.A.R.V.I.S. "
            "You are a helpful, witty, and precise AI assistant. "
            "You have access to a real-time web search tool. "
            "### RULES:"
            "1. If the user asks for **current info** (news, weather, stocks), YOU MUST use the tool."
            "2. If the user asks a personal question, answer from memory."
            "3. Always answer in a cool, British butler persona."
        )

    def generate_response(self, user_text, chat_history=[], context=""):
        # 1. Prepare System Message
        current_system_prompt = f"{self.system_prompt}\n\nLong Term Memory Context: {context}"
        messages = [SystemMessage(content=current_system_prompt)]
        
        # 2. Add Chat History (Robust Fix)
        for msg in chat_history:
            if isinstance(msg, dict):
                # Handle Dictionary format: {'role': 'human', 'content': 'hi'}
                if msg.get('role') == 'human':
                    messages.append(HumanMessage(content=msg.get('content')))
                else:
                    messages.append(AIMessage(content=msg.get('content')))
            else:
                # Handle Object format: It is already a HumanMessage/AIMessage object
                messages.append(msg)
        
        # 3. Add Current User Input
        messages.append(HumanMessage(content=user_text))

        try:
            # 4. Ask the Brain (First Pass)
            ai_msg = self.llm_with_tools.invoke(messages)

            # 5. Check if Brain wants to use the Tool
            if ai_msg.tool_calls:
                for tool_call in ai_msg.tool_calls:
                    if tool_call["name"] == "search_duckduckgo":
                        search_query = tool_call["args"]["query"]
                        print(f"🔎 J.A.R.V.I.S Searching: {search_query}")
                        
                        # Run the search
                        tool_output = search_duckduckgo(search_query)
                        
                        # Feed result back to Brain
                        messages.append(ai_msg) 
                        messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

                # 6. Final Answer (after seeing search results)
                final_response = self.llm_with_tools.invoke(messages)
                return final_response.content
            
            return ai_msg.content
            
        except Exception as e:
            print(f"❌ Brain Error: {e}")
            return f"I apologize, sir. My neural pathways are encountering an error: {e}"

# Global Instance
_brain_instance = Brain()

def get_brain_response(user_input: str, chat_history: list, long_term_memory: list):
    memory_context = "\n".join([f"- {m}" for m in long_term_memory])
    return _brain_instance.generate_response(user_input, chat_history, memory_context)