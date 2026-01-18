import os

try:
    from langchain_community.utilities import GoogleSerperAPIWrapper
except Exception:
    GoogleSerperAPIWrapper = None

from langchain_core.tools import Tool


def get_search_tool():
    # If Serper wrapper is unavailable, return a disabled tool so the agent still initializes
    if GoogleSerperAPIWrapper is None:
        def _disabled_search(query: str):
            return "Web search unavailable in this environment."

        return Tool(
            name="web_search",
            func=_disabled_search,
            description="Disabled: web_search is not installed or configured."
        )

    # Serper needs SERPER_API_KEY in .env
    search = GoogleSerperAPIWrapper()
    return Tool(
        name="web_search",
        func=search.run,
        description="Search the web for current events, news, facts, or specific information."
    )