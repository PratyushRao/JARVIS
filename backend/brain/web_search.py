from duckduckgo_search import DDGS

def search_duckduckgo(query: str):
    """
    Searches DuckDuckGo and returns a formatted string of results.
    """
    print(f"🔎 SEARCHING WEB FOR: {query}")
    try:
        # We use the Context Manager as shown in your notebook
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
            
            if not results:
                return "No results found on the web."

            # Format the output for the LLM to read easily
            formatted_results = []
            for r in results:
                formatted_results.append(
                    f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n"
                )
            
            return "\n---\n".join(formatted_results)

    except Exception as e:
        print(f"❌ Search Error: {e}")
        return f"Error searching the web: {str(e)}"