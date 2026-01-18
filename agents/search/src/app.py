import os
from typing import Dict, List, TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from tavily import TavilyClient


load_dotenv()


class State(TypedDict):
    query: str
    max_results: int
    results: List[Dict]


def search_node(state: State) -> Dict:
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return {"results": [], "error": "Missing TAVILY_API_KEY"}
    try:
        client = TavilyClient(api_key=api_key)
        max_results = state.get("max_results", 5)
        response = client.search(query=state["query"], max_results=max_results)
        return {"results": response.get("results", [])}
    except Exception as e:
        return {"results": [], "error": str(e)}


builder = StateGraph(State)
builder.add_node("search", search_node)
builder.add_edge(START, "search")
builder.add_edge("search", END)

graph = builder.compile()
