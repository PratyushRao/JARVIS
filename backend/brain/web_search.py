from langchain_core.tools import tool
from duckduckgo_search import DDGS

@tool
def search_duckduckgo(query: str) -> str:
    """
    Performs a web search using DuckDuckGo to find current information, 
    news, or facts. Use this when the user asks about recent events.
    """
    try:
        # max_results=3 keeps it fast
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
        if not results:
            return "No results found."
            
        # Format the output cleanly
        formatted_results = []
        for r in results:
            formatted_results.append(f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}")
            
        return "\n\n".join(formatted_results)
        
    except Exception as e:
        return f"Error performing web search: {e}"