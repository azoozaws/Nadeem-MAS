import os
from dotenv import load_dotenv
load_dotenv()
from tavily import TavilyClient


def search_engine(query: str, search_depth: str = "advanced") -> dict:
    """Perform a search using the Tavily API.
    Args:
        query (str): The search query.
        search_depth (str): The depth of the search, can be "basic", "medium", or "deep", "advanced".
    Returns:
        dict: The search results returned by the Tavily API.
        dict schema:
        {
        query: str,
        follow_up_questions: list[str],
        answer: str,
        images: list[str],
        results: list[{
            url: str,
            title: str,
            content: str
            score: float,
            raw_content: str
        }],
    }
    """
    client = TavilyClient(os.getenv("TAVILY_API_KEY"))
    response = client.search(
        query=query,
        search_depth=search_depth
    )
    return response

tavily_search_tools = [search_engine]